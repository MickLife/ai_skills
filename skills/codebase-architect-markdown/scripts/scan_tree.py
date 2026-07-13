#!/usr/bin/env python3
"""Scan Python/C/C++ sources and estimate analysis size using stdlib only."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path


LANGUAGES = {
    ".py": "python",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c++": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
}
BUILD_FILES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "CMakeLists.txt",
    "meson.build",
    "BUILD",
    "BUILD.bazel",
    "WORKSPACE",
    "MODULE.bazel",
    "Makefile",
    "conanfile.py",
    "conanfile.txt",
    "vcpkg.json",
}
ENTRY_HINTS = {"main.py", "app.py", "__main__.py", "main.c", "main.cpp", "main.cc"}
DEFAULT_EXCLUDES = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    "out",
    "target",
    "bin",
    "obj",
}


def _patterns(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _gitignore(root: Path) -> list[str]:
    path = root / ".gitignore"
    if not path.is_file():
        return []
    return [
        line.strip().rstrip("/")
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _matches(path: str, name: str, patterns: list[str]) -> bool:
    parts = path.split("/")
    return any(
        fnmatch.fnmatch(path, pattern)
        or fnmatch.fnmatch(name, pattern)
        or any(fnmatch.fnmatch(part, pattern) for part in parts)
        for pattern in patterns
    )


def scan(
    root: Path,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> dict:
    root = root.resolve()
    include = include or []
    excludes = list(DEFAULT_EXCLUDES) + (exclude or []) + _gitignore(root)
    files: list[dict] = []
    build_files: list[str] = []
    entry_hints: list[str] = []
    loc_by_lang: dict[str, int] = {}

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _matches(rel, path.name, excludes):
            continue
        language = LANGUAGES.get(path.suffix.lower())
        is_build = path.name in BUILD_FILES
        if include and not _matches(rel, path.name, include):
            continue
        if language is None and not is_build:
            continue
        try:
            with path.open("rb") as source:
                lines = sum(1 for _ in source)
        except OSError:
            lines = 0
        kind = language or "build"
        files.append({"path": rel, "lang": kind, "lines": lines, "tokens": lines * 4})
        loc_by_lang[kind] = loc_by_lang.get(kind, 0) + lines
        if is_build:
            build_files.append(rel)
        if path.name in ENTRY_HINTS:
            entry_hints.append(rel)

    total_tokens = sum(item["tokens"] for item in files)
    return {
        "root": str(root),
        "files": files,
        "summary": {
            "file_count": len(files),
            "total_lines": sum(item["lines"] for item in files),
            "total_tokens": total_tokens,
            "loc_by_lang": loc_by_lang,
            "build_files": sorted(build_files),
            "entry_hints": sorted(entry_hints),
            "token_budget_hint": 100_000,
            "estimated_modules": max(1, (total_tokens + 99_999) // 100_000),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--include", default="")
    parser.add_argument("--exclude", default="")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(json.dumps({"error": f"root not a dir: {args.root}"}))
        return 1
    result = scan(
        args.root,
        include=_patterns(args.include),
        exclude=_patterns(args.exclude),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
