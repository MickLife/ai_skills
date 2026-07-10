#!/usr/bin/env python3
"""Resolve file, function, method, class, or bare-symbol entry specifications."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


EXTENSIONS = {
    ".py": "python",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
}
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}


def _python_definitions(path: Path) -> list[tuple[str, int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    definitions: list[tuple[str, int, str]] = []

    def visit(node: ast.AST, prefix: str = "") -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}.{child.name}" if prefix else child.name
                kind = "class" if isinstance(child, ast.ClassDef) else "function"
                definitions.append((name, child.lineno, kind))
                visit(child, name if isinstance(child, ast.ClassDef) else prefix)
            else:
                visit(child, prefix)

    visit(tree)
    return definitions


def _cpp_definitions(path: Path) -> list[tuple[str, int, str]]:
    pattern = re.compile(
        r"^\s*(?:[A-Za-z_][\w:<>,*&\s]*?\s+)?"
        r"(?P<name>[A-Za-z_]\w*(?:::\w+)*)\s*\([^;]*\)\s*(?:const\s*)?(?:\{|$)"
    )
    results = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
    ):
        if match := pattern.search(line):
            results.append((match.group("name"), line_no, "function"))
    return results


def definitions(path: Path) -> list[tuple[str, int, str]]:
    return _python_definitions(path) if path.suffix.lower() == ".py" else _cpp_definitions(path)


def _source_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                yield path


def resolve(root: Path, spec: str) -> dict:
    normalized = spec.replace("\\", "/")
    file_part, separator, symbol = normalized.partition("::")
    explicit_file = separator or "/" in normalized or Path(normalized).suffix.lower() in EXTENSIONS

    if explicit_file:
        path = root / file_part
        if not path.is_file():
            return {"spec": spec, "error": f"file not found: {file_part}"}
        if not symbol:
            return {
                "spec": spec,
                "kind": "file",
                "file": file_part,
                "symbol": None,
                "line": None,
                "lang": EXTENSIONS.get(path.suffix.lower()),
                "candidates": [],
            }
        matches = [
            {"file": file_part, "line": line, "kind": kind}
            for name, line, kind in definitions(path)
            if name == symbol or name.endswith(f".{symbol}")
        ]
    else:
        symbol = spec
        matches = []
        for path in _source_files(root):
            rel = path.relative_to(root).as_posix()
            for name, line, kind in definitions(path):
                if name == symbol or name.endswith(f".{symbol}"):
                    matches.append({"file": rel, "line": line, "kind": kind})

    return {
        "spec": spec,
        "kind": "symbol" if separator else "bare",
        "symbol": symbol,
        "file": matches[0]["file"] if len(matches) == 1 else None,
        "line": matches[0]["line"] if len(matches) == 1 else None,
        "candidates": matches,
        "ambiguous": len(matches) > 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--entry", action="append", default=[])
    args = parser.parse_args()
    if not args.root.is_dir():
        print(json.dumps({"error": f"root not a dir: {args.root}"}))
        return 1
    root = args.root.resolve()
    print(
        json.dumps(
            {"root": str(root), "entries": [resolve(root, item) for item in args.entry]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
