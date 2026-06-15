#!/usr/bin/env python3
"""Compare two dead-code scan waves."""
from __future__ import annotations

import argparse
import json
from typing import Any, Optional


SIGNATURE_FIELDS = ["file", "line", "kind", "symbol", "message"]


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _signature(candidate: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(candidate.get(field, "")) for field in SIGNATURE_FIELDS)


def compare(previous_data: dict[str, Any], current_data: dict[str, Any]) -> dict[str, Any]:
    previous = list(previous_data.get("candidates") or [])
    current = list(current_data.get("candidates") or [])
    previous_by_key = {_signature(candidate): candidate for candidate in previous}
    current_by_key = {_signature(candidate): candidate for candidate in current}

    previous_keys = set(previous_by_key)
    current_keys = set(current_by_key)
    new_keys = current_keys - previous_keys
    resolved_keys = previous_keys - current_keys
    carried_keys = previous_keys & current_keys

    result = {
        "previous_target": previous_data.get("target", ""),
        "current_target": current_data.get("target", ""),
        "summary": {
            "previous_total": len(previous),
            "current_total": len(current),
            "new": len(new_keys),
            "resolved": len(resolved_keys),
            "carried_over": len(carried_keys),
        },
        "new": [current_by_key[key] for key in sorted(new_keys)],
        "resolved": [previous_by_key[key] for key in sorted(resolved_keys)],
        "carried_over": [current_by_key[key] for key in sorted(carried_keys)],
    }
    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="compare_waves.py",
        description="Compare two dead-code candidate JSON files.",
    )
    parser.add_argument("previous_json", help="previous wave candidate JSON")
    parser.add_argument("current_json", help="current wave candidate JSON")
    parser.add_argument(
        "--out",
        default=None,
        help="write comparison JSON to this file; print to stdout if omitted",
    )
    args = parser.parse_args(argv)

    result = compare(_load_json(args.previous_json), _load_json(args.current_json))
    text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"[compare_waves.py] wrote {args.out}")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
