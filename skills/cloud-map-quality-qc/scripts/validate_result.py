"""Validate cloud map quality inspection output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_minimal_result(result: dict) -> None:
    required_top_level = {
        "region_id",
        "inspection_version",
        "enabled_checks",
        "findings",
        "summary",
        "needs_human_review",
    }
    missing_top_level = required_top_level - set(result)
    if missing_top_level:
        raise SystemExit(f"Missing top-level fields: {sorted(missing_top_level)}")

    if not isinstance(result["enabled_checks"], list) or not result["enabled_checks"]:
        raise SystemExit("enabled_checks must be a non-empty array")
    if not isinstance(result["findings"], list):
        raise SystemExit("findings must be an array")

    required_finding = {
        "issue_type",
        "subtype",
        "confidence",
        "severity",
        "location",
        "evidence",
        "reason",
        "possible_false_positives",
        "needs_human_review",
    }
    for index, finding in enumerate(result["findings"]):
        missing_finding = required_finding - set(finding)
        if missing_finding:
            raise SystemExit(f"Finding {index} missing fields: {sorted(missing_finding)}")
        if not 0 <= finding["confidence"] <= 1:
            raise SystemExit(f"Finding {index} confidence must be between 0 and 1")
        if finding["severity"] not in {"low", "medium", "high", "critical"}:
            raise SystemExit(f"Finding {index} severity is invalid: {finding['severity']}")
        if not isinstance(finding["evidence"], list) or not finding["evidence"]:
            raise SystemExit(f"Finding {index} evidence must be a non-empty array")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate cloud map quality inspection JSON output.")
    parser.add_argument("--schema", required=True, help="JSON schema path.")
    parser.add_argument("--registry", required=True, help="Issue registry JSON path.")
    parser.add_argument("--result", required=True, help="Result JSON path.")
    args = parser.parse_args()

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))

    try:
        import jsonschema
    except ImportError:
        validate_minimal_result(result)
    else:
        jsonschema.validate(instance=result, schema=schema)

    issues = {issue["issue_type"]: set(issue.get("subtypes", [])) for issue in registry.get("issues", [])}
    for finding in result.get("findings", []):
        issue_type = finding["issue_type"]
        subtype = finding["subtype"]
        if issue_type not in issues:
            raise SystemExit(f"Unknown issue_type: {issue_type}")
        if subtype not in issues[issue_type]:
            raise SystemExit(f"Unknown subtype for {issue_type}: {subtype}")

    print("OK")


if __name__ == "__main__":
    main()
