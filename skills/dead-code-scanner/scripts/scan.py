#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Candidate dead-code scanner for the dead-code-scanner skill.

Aggregates vulture + ruff static analysis into a structured JSON candidate
list for AI review. This script only enumerates candidates; it does not decide
what is safe to delete.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Candidate:
    id: str
    tool: str
    file: str
    line: int
    kind: str
    symbol: str
    message: str
    confidence: Optional[int] = None
    rule: Optional[str] = None
    in_whitelist: bool = False


# ---- vulture ----------------------------------------------------------------

_VULTURE_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):\s*(?P<msg>.+?)\s*"
    r"\((?P<conf>\d+)% confidence\)\s*$"
)

_KIND_MAP = [
    ("unreachable", "unreachable"),
    ("unused import", "unused_import"),
    ("unused variable", "unused_variable"),
    ("unused function", "unused_function"),
    ("unused method", "unused_method"),
    ("unused class", "unused_class"),
    ("unused property", "unused_property"),
    ("unused attribute", "unused_attribute"),
    ("unused", "unused_other"),
]


def _classify_vulture(message: str) -> str:
    lowered = message.lower()
    for keyword, kind in _KIND_MAP:
        if keyword in lowered:
            return kind
    return "other"


def _extract_symbol(message: str) -> str:
    match = re.search(r"'([^']+)'", message)
    return match.group(1) if match else ""


def _module_missing(name: str) -> bool:
    try:
        __import__(name)
        return False
    except ImportError:
        return True


def run_vulture(
    target: str,
    min_confidence: int,
    exclude: str,
) -> list[Candidate]:
    if _module_missing("vulture"):
        return []

    cmd = [
        sys.executable,
        "-m",
        "vulture",
        target,
        "--min-confidence",
        str(min_confidence),
    ]
    if exclude:
        cmd += ["--exclude", exclude]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    candidates: list[Candidate] = []
    for raw in proc.stdout.splitlines():
        match = _VULTURE_RE.match(raw.strip())
        if not match:
            continue
        message = match.group("msg")
        candidates.append(
            Candidate(
                id="",
                tool="vulture",
                file=match.group("file"),
                line=int(match.group("line")),
                kind=_classify_vulture(message),
                symbol=_extract_symbol(message),
                message=message,
                confidence=int(match.group("conf")),
            )
        )
    return candidates


# ---- ruff -------------------------------------------------------------------

_RUFF_KIND = {
    "F401": "unused_import",
    "F811": "redefined_unused",
    "F841": "unused_variable",
}


def run_ruff(target: str) -> list[Candidate]:
    if _module_missing("ruff"):
        return []

    cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        target,
        "--select",
        "F401,F811,F841,ERA001",
        "--output-format",
        "json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []

    candidates: list[Candidate] = []
    for item in items:
        code = item.get("code") or ""
        if code in _RUFF_KIND:
            kind = _RUFF_KIND[code]
        elif code.startswith("ERA"):
            kind = "commented_dead_code"
        else:
            kind = "other"

        location = item.get("location") or {}
        candidates.append(
            Candidate(
                id="",
                tool="ruff",
                file=item.get("filename", ""),
                line=location.get("row", 0),
                kind=kind,
                symbol="",
                message=item.get("message", ""),
                rule=code,
            )
        )
    return candidates


# ---- helpers ----------------------------------------------------------------

def _read_whitelist_symbols(whitelist: Optional[str]) -> set[str]:
    if not whitelist or not os.path.exists(whitelist):
        return set()

    symbols: set[str] = set()
    with open(whitelist, encoding="utf-8") as handle:
        for line in handle:
            for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", line):
                symbols.add(match.group(0))
    return symbols


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description=(
            "Aggregate vulture + ruff dead-code candidates into structured "
            "JSON for AI review. This tool only enumerates candidates; it "
            "does not decide what is safe to delete."
        ),
        epilog=(
            "Examples:\n"
            "  python scan.py ./src\n"
            "  python scan.py ./src --min-confidence 80 --exclude '*/tests/*'\n"
            "  python scan.py ./src --whitelist whitelist.py --out report.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="directory or file to scan, e.g. ./src")
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=60,
        help=(
            "vulture confidence threshold 0-100 (default 60). "
            "Raise to reduce false positives"
        ),
    )
    parser.add_argument(
        "--exclude",
        default="",
        help="comma-separated exclude globs, e.g. '*/tests/*,*/migrations/*'",
    )
    parser.add_argument(
        "--whitelist",
        default=None,
        help="vulture whitelist file; matched symbols get flagged in_whitelist",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="write JSON to this file; print to stdout if omitted",
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.target):
        print(f"[scan.py] target not found: {args.target}", file=sys.stderr)
        return 2

    candidates = [
        *run_vulture(
            args.target,
            args.min_confidence,
            args.exclude,
        ),
        *run_ruff(args.target),
    ]

    whitelist_symbols = _read_whitelist_symbols(args.whitelist)
    for index, candidate in enumerate(candidates, start=1):
        candidate.id = f"DC{index:06d}"
        if candidate.symbol and candidate.symbol in whitelist_symbols:
            candidate.in_whitelist = True

    summary: dict[str, int] = {}
    for candidate in candidates:
        summary[candidate.kind] = summary.get(candidate.kind, 0) + 1

    tools_available = {
        "vulture": not _module_missing("vulture"),
        "ruff": not _module_missing("ruff"),
    }

    result = {
        "target": args.target,
        "tools_available": tools_available,
        "total": len(candidates),
        "summary_by_kind": summary,
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"[scan.py] wrote {args.out} ({len(candidates)} candidates)")
    else:
        print(text)

    if not any(tools_available.values()):
        print(
            "[scan.py] WARNING: vulture / ruff not found. "
            "Run pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
