#!/usr/bin/env python3
# coding: utf-8
"""
scan_tree.py — codebase-architect 侦察脚本
扫描根目录，产出带每文件行数/token 估算的文件清单（尊重 .gitignore）。
纯标准库，离线运行，向 stdout 输出 JSON。

用法:
    python scan_tree.py --root /path/to/repo [--include "*.py,*.cpp,*.h"] [--exclude "tests,build"]

输出字段:
    { "root": "...", "files": [{path, lang, lines, tokens}], "summary": {...} }
"""
import argparse
import fnmatch
import json
import os
import sys

LANG_MAP = {
    ".py": "python",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c++": "cpp",
    ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp", ".h++": "cpp",
}

DEFAULT_EXCLUDES = [
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "build", "dist", "out", "target", "bin", "obj",
    ".pytest_cache", ".mypy_cache", ".tox", ".eggs", "*.egg-info",
    "*.pyc", "*.pyo", "*.pyd", "*.o", "*.obj", "*.a", "*.so", "*.dll", "*.dylib",
    ".idea", ".vscode", ".cache", "coverage", ".coverage", "htmlcov",
]

BUILD_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "poetry.lock",
    "requirements.txt", "requirements-dev.txt", "conda.yml",
    "CMakeLists.txt", "meson.build", "BUILD", "BUILD.bazel", "WORKSPACE",
    "MODULE.bazel", "Makefile", "conanfile.py", "conanfile.txt", "vcpkg.json",
}

ENTRY_HINTS = {"main.py", "app.py", "__main__.py", "main.c", "main.cpp", "main.cc"}


def load_gitignore(root):
    """读取 .gitignore，返回 patterns 列表（朴素实现，不处理 glob 否定等复杂语义）。"""
    patterns = []
    gi = os.path.join(root, ".gitignore")
    if os.path.isfile(gi):
        with open(gi, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)
    return patterns


def excluded(rel_path, name, excludes, gitignore_patterns, include_globs):
    # include 过滤（若指定，仅保留匹配项）
    if include_globs:
        if not any(fnmatch.fnmatch(name, g) or fnmatch.fnmatch(rel_path, g)
                   for g in include_globs):
            return True
    # 默认 + 用户 exclude
    for pat in excludes:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_path, pat):
            return True
    # gitignore 朴素匹配（按目录名/文件名/通配）
    parts = rel_path.replace("\\", "/").split("/")
    for pat in gitignore_patterns:
        pat = pat.rstrip("/")
        if pat.startswith("/"):
            pat = pat[1:]
            if rel_path.replace("\\", "/").startswith(pat) or fnmatch.fnmatch(rel_path, pat):
                return True
        else:
            if any(fnmatch.fnmatch(p, pat) for p in parts):
                return True
    return False


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--include", default="", help="逗号分隔 glob，指定后仅保留匹配项")
    ap.add_argument("--exclude", default="", help="逗号分隔，与默认排除合并")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(json.dumps({"error": f"root not a dir: {root}"}))
        sys.exit(1)

    include_globs = [g.strip() for g in args.include.split(",") if g.strip()]
    user_excludes = [e.strip() for e in args.exclude.split(",") if e.strip()]
    excludes = DEFAULT_EXCLUDES + user_excludes
    gi_patterns = load_gitignore(root)

    files = []
    build_found = set()
    entry_found = set()
    lang_loc = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # 原地剪枝，避免进入排除目录
        dirnames[:] = [d for d in dirnames
                       if not any(fnmatch.fnmatch(d, p) for p in excludes)
                       and d not in (".git",)]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/")
            if excluded(rel, fn, excludes, gi_patterns, include_globs):
                continue
            ext = os.path.splitext(fn)[1].lower()
            lang = LANG_MAP.get(ext)
            if lang is None and fn in BUILD_FILES:
                lang = "build"
            if lang is None:
                # 非目标语言且非构建文件，跳过（但记录构建/入口文件名）
                if fn in BUILD_FILES:
                    build_found.add(rel)
                if fn in ENTRY_HINTS:
                    entry_found.add(rel)
                continue
            full = os.path.join(dirpath, fn)
            lines = count_lines(full)
            tokens = lines * 4  # 启发式
            files.append({
                "path": rel,
                "lang": lang,
                "lines": lines,
                "tokens": tokens,
            })
            lang_loc[lang] = lang_loc.get(lang, 0) + lines
            if fn in BUILD_FILES:
                build_found.add(rel)
            if fn in ENTRY_HINTS:
                entry_found.add(rel)

    total_loc = sum(lang_loc.values())
    total_tokens = sum(f["tokens"] for f in files)
    summary = {
        "file_count": len(files),
        "total_lines": total_loc,
        "total_tokens": total_tokens,
        "loc_by_lang": lang_loc,
        "build_files": sorted(build_found),
        "entry_hints": sorted(entry_found),
        "token_budget_hint": 100000,
        "estimated_modules": max(1, total_tokens // 100000),
    }
    print(json.dumps({"root": root, "files": files, "summary": summary},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
