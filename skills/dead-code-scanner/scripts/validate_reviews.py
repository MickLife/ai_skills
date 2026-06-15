#!/usr/bin/env python3
"""Validate chunk review coverage and required report fields."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any, Optional


VALID_STATUSES = {
    "confirmed_deletable",
    "suspected_deletable",
    "false_positive",
}

REQUIRED_FIELDS = [
    "candidate_id",
    "status",
    "file",
    "candidate_line",
    "symbol",
    "kind",
    "removal_range",
    "removable_lines",
    "evidence",
    "risk",
    "recommended_action",
]


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _review_results(review_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for document in review_docs:
        results.extend(document.get("results") or [])
    return results


def _summary(total_candidates: int, results: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    status_counts = Counter(str(result.get("status")) for result in results)
    removable_total = 0
    for result in results:
        if result.get("status") == "confirmed_deletable":
            try:
                removable_total += int(result.get("removable_lines", 0))
            except (TypeError, ValueError):
                pass

    return {
        "total_candidates": total_candidates,
        "reviewed_candidates": len(results),
        "confirmed_deletable": status_counts["confirmed_deletable"],
        "suspected_deletable": status_counts["suspected_deletable"],
        "false_positive": status_counts["false_positive"],
        "total_removable_lines": removable_total,
        "review_status": "COMPLETE" if not errors else "INCOMPLETE",
    }


def validate(
    candidates_data: dict[str, Any],
    review_docs: list[dict[str, Any]],
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = list(candidates_data.get("candidates") or [])
    expected_ids = [str(candidate.get("id")) for candidate in candidates]
    expected_set = set(expected_ids)
    results = _review_results(review_docs)
    errors: list[str] = []

    seen_ids: list[str] = []
    for result in results:
        candidate_id = str(result.get("candidate_id", ""))
        seen_ids.append(candidate_id)

        if candidate_id not in expected_set:
            errors.append(f"Unknown candidate {candidate_id}")

        for field in REQUIRED_FIELDS:
            if field not in result:
                errors.append(f"Review {candidate_id} missing required field {field}")

        status = result.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"Review {candidate_id} has invalid status {status}")

        if "removable_lines" in result:
            try:
                int(result["removable_lines"])
            except (TypeError, ValueError):
                errors.append(f"Review {candidate_id} has non-numeric removable_lines")

    if plan:
        assigned_by_chunk = {
            str(chunk.get("chunk_id")): set(str(candidate_id) for candidate_id in chunk.get("candidate_ids", []))
            for chunk in plan.get("chunks", [])
        }
        for document in review_docs:
            chunk_id = str(document.get("chunk_id", ""))
            assigned_ids = assigned_by_chunk.get(chunk_id)
            if assigned_ids is None:
                errors.append(f"Review chunk {chunk_id} is not present in plan")
                continue
            for result in document.get("results") or []:
                candidate_id = str(result.get("candidate_id", ""))
                if candidate_id not in assigned_ids:
                    errors.append(f"Review {candidate_id} is not assigned to chunk {chunk_id}")

    seen_counts = Counter(seen_ids)
    for candidate_id, count in seen_counts.items():
        if candidate_id and count > 1:
            errors.append(f"Duplicate review for candidate {candidate_id}")

    seen_set = set(seen_ids)
    for candidate_id in expected_ids:
        if candidate_id not in seen_set:
            errors.append(f"Missing review for candidate {candidate_id}")

    summary = _summary(len(candidates), results, errors)
    return {
        "valid": not errors,
        "errors": errors,
        "summary": summary,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_reviews.py",
        description="Validate dead-code chunk review coverage and schema.",
    )
    parser.add_argument("candidates_json", help="candidate JSON produced by scan.py")
    parser.add_argument("review_json", nargs="+", help="one or more chunk review JSON files")
    parser.add_argument(
        "--plan",
        default=None,
        help="optional review plan JSON to validate chunk membership",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="write validation JSON to this file; print to stdout if omitted",
    )
    args = parser.parse_args(argv)

    candidates_data = _load_json(args.candidates_json)
    review_docs = [_load_json(path) for path in args.review_json]
    plan = _load_json(args.plan) if args.plan else None
    result = validate(candidates_data, review_docs, plan=plan)
    text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"[validate_reviews.py] wrote {args.out}")
    else:
        print(text)

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
