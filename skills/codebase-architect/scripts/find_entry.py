#!/usr/bin/env python3
# coding: utf-8
"""
find_entry.py — codebase-architect 入口解析脚本
把用户给出的入口规格解析到具体 (file, symbol, line)。
纯标准库，离线运行，向 stdout 输出 JSON。

入口规格形式:
    path/to/file.py                  整文件作为根
    path/to/file.py::function_name   文件内某函数
    path/to/file.py::ClassName.method
    handle_request                   裸符号名（在根下 grep 定义）

用法:
    python find_entry.py --root /path --entry "src/core/engine.py::run_pipeline" --entry "handle_request"

输出:
    { "root": "...", "entries": [{spec, file, symbol, line, kind, candidates}] }
"""
import argparse
import json
import os
import re
import sys

LANG_EXTS = {
    "python": (".py",),
    "c": (".c", ".h"),
    "cpp": (".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hh", ".hxx", ".h++", ".h"),
}

# 定义模式（按语言）
PY_DEF = re.compile(r"^\s*(async\s+def|def|class)\s+({name})\b")
CPP_DEF = re.compile(r"^\s*(?:[A-Za-z_][\w:<>,\*\&\s]*?\s)?({name})\s*\(")


def find_symbol_in_file(path, symbol, lang):
    """在单个文件中查找 symbol 定义行，返回 line 号列表。"""
    pat = PY_DEF if lang == "python" else CPP_DEF
    pat = pat.pattern.format(name=re.escape(symbol))
    regex = re.compile(pat)
    hits = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if regex.search(line):
                    hits.append(i)
    except Exception:
        pass
    return hits


def detect_lang(path):
    ext = os.path.splitext(path)[1].lower()
    for lang, exts in LANG_EXTS.items():
        if ext in exts:
            return lang
    return None


def resolve_file_entry(root, file_rel, symbol):
    """处理 file 或 file::symbol 形式。"""
    full = os.path.join(root, file_rel)
    if not os.path.isfile(full):
        return {"spec": None, "error": f"file not found: {file_rel}"}
    lang = detect_lang(full)
    if symbol:
        lines = find_symbol_in_file(full, symbol, lang) if lang else []
        return {
            "spec": f"{file_rel}::{symbol}",
            "file": file_rel,
            "symbol": symbol,
            "kind": "symbol",
            "lang": lang,
            "candidates": [{"line": l} for l in lines],
            "line": lines[0] if lines else None,
        }
    return {
        "spec": file_rel,
        "file": file_rel,
        "symbol": None,
        "kind": "file",
        "lang": lang,
        "candidates": [],
        "line": None,
    }


def resolve_bare_symbol(root, symbol):
    """裸符号名：在根下所有源文件中 grep 定义。"""
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            lang = None
            for l, exts in LANG_EXTS.items():
                if ext in exts:
                    lang = l
                    break
            if lang is None:
                continue
            full = os.path.join(dirpath, fn)
            hits = find_symbol_in_file(full, symbol, lang)
            for ln in hits:
                results.append({
                    "file": os.path.relpath(full, root).replace("\\", "/"),
                    "line": ln,
                    "lang": lang,
                })
    return {
        "spec": symbol,
        "symbol": symbol,
        "kind": "bare",
        "candidates": results,
        "file": results[0]["file"] if len(results) == 1 else None,
        "line": results[0]["line"] if len(results) == 1 else None,
        "ambiguous": len(results) > 1,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--entry", action="append", default=[],
                    help="可多次传入；形式 file / file::symbol / bare_symbol")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(json.dumps({"error": f"root not a dir: {root}"}))
        sys.exit(1)

    entries = []
    for spec in args.entry:
        if "::" in spec:
            file_rel, symbol = spec.split("::", 1)
            entries.append(resolve_file_entry(root, file_rel.replace("\\", "/"), symbol))
        elif "/" in spec or os.path.splitext(spec)[1].lower() in {
            e for exts in LANG_EXTS.values() for e in exts}:
            entries.append(resolve_file_entry(root, spec.replace("\\", "/"), None))
        else:
            entries.append(resolve_bare_symbol(root, spec))

    print(json.dumps({"root": root, "entries": entries},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
