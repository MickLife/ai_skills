#!/usr/bin/env python3
"""Validate generated Markdown architecture documents using the standard library."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]+\}\}")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LONG_TOKEN_RE = re.compile(r"(?:[A-Za-z0-9_.:-]+[/\\]){3,}[A-Za-z0-9_.:-]+")
DESIGN_INTENT = "设计意图"
KEY_INTERPRETATION = "关键解读"


def _is_local_link(target: str) -> bool:
    lowered = target.lower()
    return not (
        lowered.startswith(("http://", "https://", "data:", "#", "mailto:"))
    )


def _diagram_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """Return inclusive line-index ranges for Mermaid fences and SVG images."""
    ranges: list[tuple[int, int]] = []
    mermaid_start: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if mermaid_start is None and stripped.startswith("```mermaid"):
            mermaid_start = index
        elif mermaid_start is not None and stripped.startswith("```"):
            ranges.append((mermaid_start, index))
            mermaid_start = None
        elif IMAGE_RE.search(line):
            target = IMAGE_RE.search(line).group(1).split("#", 1)[0]
            if target.lower().endswith(".svg"):
                ranges.append((index, index))
    return ranges


def _section_bounds(lines: list[str], start: int, end: int) -> tuple[int, int]:
    """Limit diagram-caption checks to the surrounding Markdown section."""
    section_start = 0
    for index in range(start - 1, -1, -1):
        if HEADING_RE.match(lines[index]):
            section_start = index + 1
            break

    section_end = len(lines)
    for index in range(end + 1, len(lines)):
        if HEADING_RE.match(lines[index]):
            section_end = index
            break
    return section_start, section_end


def validate_document(path: Path) -> list[str]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        errors.append(f"发现未替换占位符：{', '.join(sorted(set(placeholders)))}")

    fence_lines = [line for line in lines if line.lstrip().startswith("```")]
    if len(fence_lines) % 2:
        errors.append("代码围栏未闭合：``` 数量不是偶数")

    for target in IMAGE_RE.findall(text):
        clean_target = target.split("#", 1)[0]
        if _is_local_link(clean_target):
            asset = (path.parent / clean_target).resolve()
            if not asset.is_file():
                errors.append(f"图片或资源不存在：{target}")

    for target in LINK_RE.findall(text):
        clean_target = target.split("#", 1)[0]
        if clean_target and _is_local_link(target):
            linked_file = (path.parent / clean_target).resolve()
            if not linked_file.exists():
                errors.append(f"本地链接不存在：{target}")

    headings = [
        match.group(2).strip()
        for line in lines
        if (match := HEADING_RE.match(line))
    ]
    duplicates = [name for name, count in Counter(headings).items() if count > 1]
    if duplicates:
        errors.append(f"发现重复标题：{', '.join(sorted(duplicates))}")

    for start, end in _diagram_ranges(lines):
        section_start, section_end = _section_bounds(lines, start, end)
        before = "\n".join(lines[section_start:start])
        after = "\n".join(lines[end + 1 : section_end])
        if DESIGN_INTENT not in before:
            errors.append(f"第 {start + 1} 行图形前缺少“设计意图”")
        if KEY_INTERPRETATION not in after:
            errors.append(f"第 {end + 1} 行图形后缺少“关键解读”")

    in_table = False
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        is_table_line = stripped.startswith("|") and stripped.endswith("|")
        in_table = is_table_line or (in_table and "|" in stripped)
        if is_table_line and (
            LONG_TOKEN_RE.search(stripped)
            or any(len(cell.strip(" `")) > 64 for cell in stripped.split("|"))
        ):
            errors.append(
                f"第 {line_no} 行存在宽表格风险：长路径/类名应改用列表或分段"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a generated Markdown architecture document."
    )
    parser.add_argument("document", type=Path)
    args = parser.parse_args()

    errors = validate_document(args.document)
    if errors:
        for item in errors:
            print(f"ERROR: {item}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
