#!/usr/bin/env python3
"""Create review chunks from dead-code candidates."""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import PurePath
from typing import Any, Optional


def _candidate_file(candidate: dict[str, Any]) -> str:
    return str(candidate.get("file") or "")


def _candidate_dir(candidate: dict[str, Any]) -> str:
    path = PurePath(_candidate_file(candidate))
    parent = str(path.parent)
    return "" if parent == "." else parent


def _split(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def build_plan(
    candidates_data: dict[str, Any],
    chunk_size: int,
    source_path: str,
) -> dict[str, Any]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")

    candidates = list(candidates_data.get("candidates") or [])
    by_file: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for candidate in candidates:
        by_file.setdefault(_candidate_file(candidate), []).append(candidate)

    chunks: list[dict[str, Any]] = []
    for file_path, file_candidates in by_file.items():
        for part in _split(file_candidates, chunk_size):
            chunk_number = len(chunks) + 1
            chunks.append(
                {
                    "chunk_id": f"CHUNK_{chunk_number:03d}",
                    "status": "pending",
                    "group_key": file_path,
                    "allowed_paths": [file_path],
                    "candidate_ids": [str(candidate["id"]) for candidate in part],
                    "candidates": part,
                }
            )

    return {
        "candidate_file": source_path,
        "target": candidates_data.get("target", ""),
        "total_candidates": len(candidates),
        "chunk_size": chunk_size,
        "chunk_count": len(chunks),
        "dispatch_required": len(candidates) > 30,
        "parallel_dispatch_required": len(candidates) > 80,
        "chunks": chunks,
        "grouping": {
            "strategy": "file",
            "directories": sorted(
                {directory for candidate in candidates if (directory := _candidate_dir(candidate))}
            ),
        },
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plan_review.py",
        description="Create chunked review plans from dead-code candidates.",
    )
    parser.add_argument("candidates_json", help="candidate JSON produced by scan.py")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=25,
        help="maximum candidates per chunk (default 25)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="write JSON plan to this file; print to stdout if omitted",
    )
    args = parser.parse_args(argv)

    with open(args.candidates_json, encoding="utf-8") as handle:
        candidates_data = json.load(handle)

    plan = build_plan(candidates_data, args.chunk_size, args.candidates_json)
    text = json.dumps(plan, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"[plan_review.py] wrote {args.out} ({plan['chunk_count']} chunks)")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
