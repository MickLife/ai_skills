#!/usr/bin/env python3
"""Build a best-effort Python import and C/C++ include graph."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


PY_EXTS = {".py"}
CPP_EXTS = {".c", ".h", ".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hh", ".hxx"}
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", "node_modules"}
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')
CMAKE_TARGET_RE = re.compile(r"add_(library|executable)\s*\(\s*(\w+)", re.I)
CMAKE_SUBDIR_RE = re.compile(r"add_subdirectory\s*\(\s*([^\s)]+)", re.I)
CMAKE_FETCH_RE = re.compile(r"FetchContent_Declare\s*\(\s*(\w+)", re.I)


def _sources(root: Path) -> list[tuple[Path, str, str]]:
    items = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        suffix = path.suffix.lower()
        language = "python" if suffix in PY_EXTS else "cpp" if suffix in CPP_EXTS else None
        if language:
            items.append((path, rel.as_posix(), language))
    return items


def _python_modules(files: list[tuple[Path, str, str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _, rel, language in files:
        if language != "python":
            continue
        module = rel[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        mapping[module] = rel
        if module.startswith("src."):
            mapping[module[4:]] = rel
    return mapping


def _scan_python(path: Path, rel: str, modules: dict[str, str]) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    edges: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(
                    {
                        "from": rel,
                        "to_module": alias.name,
                        "kind": "import",
                        "line": node.lineno,
                        "resolved": modules.get(alias.name),
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            edges.append(
                {
                    "from": rel,
                    "to_module": module,
                    "kind": "from_import",
                    "line": node.lineno,
                    "level": node.level,
                    "names": [alias.name for alias in node.names],
                    "resolved": None if node.level else modules.get(module),
                }
            )
    return edges


def _scan_cpp(
    path: Path,
    rel: str,
    by_basename: dict[str, list[str]],
) -> list[dict]:
    edges = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
    ):
        if match := INCLUDE_RE.match(line):
            delimiter, target = match.groups()
            candidates = by_basename.get(Path(target).name, [])
            edges.append(
                {
                    "from": rel,
                    "to_include": target,
                    "kind": "include",
                    "line": line_no,
                    "system": delimiter == "<",
                    "resolved": candidates[0] if delimiter == '"' and len(candidates) == 1 else None,
                    "candidates": candidates,
                }
            )
    return edges


def _scan_cmake(root: Path) -> dict:
    result = {"targets": [], "subdirs": [], "fetch": []}
    for path in root.rglob("CMakeLists.txt"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in CMAKE_TARGET_RE.finditer(text):
            result["targets"].append(
                {"name": match.group(2), "type": match.group(1).lower(), "file": rel}
            )
        result["subdirs"].extend(
            {"dir": match.group(1), "file": rel}
            for match in CMAKE_SUBDIR_RE.finditer(text)
        )
        result["fetch"].extend(
            {"name": match.group(1), "file": rel}
            for match in CMAKE_FETCH_RE.finditer(text)
        )
    return result


def scan(root: Path) -> dict:
    root = root.resolve()
    files = _sources(root)
    modules = _python_modules(files)
    by_basename: dict[str, list[str]] = {}
    for _, rel, _ in files:
        by_basename.setdefault(Path(rel).name, []).append(rel)

    edges = []
    for path, rel, language in files:
        if language == "python":
            edges.extend(_scan_python(path, rel, modules))
        else:
            edges.extend(_scan_cpp(path, rel, by_basename))

    unresolved = [edge for edge in edges if edge.get("resolved") is None]
    return {
        "root": str(root),
        "nodes": [{"file": rel, "lang": language} for _, rel, language in files],
        "edges": edges,
        "unresolved": unresolved,
        "cmake": _scan_cmake(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--format", default="json", choices=["json"])
    args = parser.parse_args()
    if not args.root.is_dir():
        print(json.dumps({"error": f"root not a dir: {args.root}"}))
        return 1
    print(json.dumps(scan(args.root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
