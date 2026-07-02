#!/usr/bin/env python3
# coding: utf-8
"""
deps_scan.py — codebase-architect 依赖图脚本
构建 Python import / C/C++ #include 静态依赖图。
纯标准库，离线运行，向 stdout 输出 JSON。

用法:
    python deps_scan.py --root /path/to/repo --format json

输出:
    {
      "root": "...",
      "nodes": [{file, lang}],
      "edges": [{from, to, kind, line, resolved}],
      "unresolved": [{from, ref, line, kind}]
    }
"""
import argparse
import ast
import json
import os
import re
import sys

PY_EXTS = (".py",)
C_EXTS = (".c", ".h", ".cpp", ".cc", ".cxx", ".c++")
CPP_HDR_EXTS = (".hpp", ".hh", ".hxx", ".h++")
CPP_EXTS = CPP_HDR_EXTS + (".cpp", ".cc", ".cxx", ".c++")
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')

CMAKE_INCLUDE_RE = re.compile(r'target_include_directories\s*\(\s*(\w+)[^\)]*INCLUDE_DIRECTORIES\s+([^\)]+)', re.I)
CMAKE_SUBDIR_RE = re.compile(r'add_subdirectory\s*\(\s*([^)\s]+)')
CMAKE_FETCH_RE = re.compile(r'FetchContent_Declare\s*\(\s*(\w+)')
CMAKE_ADDLIB_RE = re.compile(r'add_library\s*\(\s*(\w+)')
CMAKE_ADDEXE_RE = re.compile(r'add_executable\s*\(\s*(\w+)')


def lang_of(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in PY_EXTS:
        return "python"
    if ext in C_EXTS:
        return "c"
    if ext in CPP_EXTS:
        return "cpp"
    return None


def walk_sources(root):
    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__",
                                            "build", "dist", ".venv", "venv")]
        for f in fn:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            lang = lang_of(rel)
            if lang:
                files.append((rel, full, lang))
    return files


def py_module_name(rel, roots):
    """把相对路径转为点分模块名，按已知包根。"""
    rel_no_ext = rel[:-3] if rel.endswith(".py") else rel
    for r in roots:
        if rel_no_ext.startswith(r + "/"):
            return rel_no_ext[len(r) + 1:].replace("/", ".")
    return rel_no_ext.replace("/", ".")


def scan_python(full, rel, modname):
    edges = []
    unresolved = []
    try:
        src = open(full, encoding="utf-8", errors="ignore").read()
        tree = ast.parse(src, filename=full)
    except Exception:
        return edges, unresolved
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                edges.append({
                    "from": rel, "to_module": n.name, "kind": "import",
                    "line": node.lineno, "alias": n.asname,
                    "resolved": None,
                })
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            level = node.level
            edges.append({
                "from": rel, "to_module": mod, "kind": "from_import",
                "line": node.lineno, "level": level,
                "names": [n.name for n in node.names],
                "is_relative": level > 0,
                "resolved": None,
            })
    return edges, unresolved


INCLUDE_RE_C = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')


def scan_c_cpp(full, rel, lang):
    edges = []
    try:
        with open(full, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                m = INCLUDE_RE_C.match(line)
                if m:
                    quote, target = m.group(1), m.group(2)
                    edges.append({
                        "from": rel,
                        "to_include": target,
                        "kind": "include",
                        "line": i,
                        "system": quote == "<",
                        "resolved": None,
                    })
    except Exception:
        pass
    return edges


def resolve_python(edges, files_set, mod_to_file):
    for e in edges:
        if e["kind"] not in ("import", "from_import"):
            continue
        mod = e["to_module"]
        cand = mod_to_file.get(mod) or mod_to_file.get(mod + ".__init__")
        if cand:
            e["resolved"] = cand
        else:
            e["resolved"] = None


def resolve_c_cpp(edges, files_by_basename, files_set):
    for e in edges:
        if e["kind"] != "include":
            continue
        target = e["to_include"]
        # 系统头一律标未解析（需构建系统 include 路径）
        if e["system"]:
            e["resolved"] = None
            continue
        # 引号头：先相对当前文件目录
        base = os.path.basename(target)
        cands = files_by_basename.get(base, [])
        e["resolved"] = cands[0] if cands else None


def detect_py_roots(files):
    """简单包根推断：含 __init__.py 的目录的顶层祖先。"""
    init_dirs = {os.path.dirname(r) for r, _, _ in files if os.path.basename(r) == "__init__.py"}
    roots = set()
    for d in init_dirs:
        top = d.split("/")[0]
        roots.add(top)
    return sorted(roots)


def scan_cmake(root):
    """从 CMakeLists.txt 提取 target / include 路径 / 跨仓线索。"""
    info = {"targets": [], "include_dirs": [], "subdirs": [], "fetch": []}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git",)]
        for f in fn:
            if f == "CMakeLists.txt":
                full = os.path.join(dp, f)
                try:
                    txt = open(full, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                rel = os.path.relpath(full, root).replace("\\", "/")
                for m in CMAKE_ADDLIB_RE.finditer(txt):
                    info["targets"].append({"name": m.group(1), "type": "library", "file": rel})
                for m in CMAKE_ADDEXE_RE.finditer(txt):
                    info["targets"].append({"name": m.group(1), "type": "executable", "file": rel})
                for m in CMAKE_SUBDIR_RE.finditer(txt):
                    info["subdirs"].append({"dir": m.group(1), "file": rel})
                for m in CMAKE_FETCH_RE.finditer(txt):
                    info["fetch"].append({"name": m.group(1), "file": rel})
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--format", default="json", choices=["json"])
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(json.dumps({"error": f"root not a dir: {root}"}))
        sys.exit(1)

    files = walk_sources(root)
    files_set = {r for r, _, _ in files}

    # Python 包根与模块映射
    py_files = [(r, f, l) for (r, f, l) in files if l == "python"]
    py_roots = detect_py_roots(py_files)
    mod_to_file = {}
    for r, full, l in py_files:
        mod = py_module_name(r, py_roots)
        mod_to_file[mod] = r
        if os.path.basename(r) == "__init__.py":
            mod_to_file.setdefault(mod + ".__init__", r)

    # 扫描
    all_edges = []
    for r, full, l in files:
        if l == "python":
            e, _ = scan_python(full, r, None)
            all_edges.extend(e)
        else:
            all_edges.extend(scan_c_cpp(full, r, l))

    files_by_basename = {}
    for r, _, _ in files:
        files_by_basename.setdefault(os.path.basename(r), []).append(r)

    resolve_python(all_edges, files_set, mod_to_file)
    resolve_c_cpp(all_edges, files_by_basename, files_set)

    unresolved = [e for e in all_edges if e.get("resolved") is None and
                  (e["kind"] == "include" and e["system"]) or
                  (e["kind"] in ("import", "from_import") and not e.get("is_relative"))]

    cmake = scan_cmake(root)

    nodes = [{"file": r, "lang": l} for (r, _, l) in files]
    out = {
        "root": root,
        "python_roots": py_roots,
        "nodes": nodes,
        "edges": all_edges,
        "unresolved": unresolved,
        "cmake": cmake,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
