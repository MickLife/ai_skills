from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "skills" / "dead-code-scanner"
sys.path.insert(0, str(ROOT / "scripts"))

import validate_reviews  # noqa: E402


def _candidate(candidate_id: str) -> dict[str, object]:
    return {
        "id": candidate_id,
        "file": "src/a.py",
        "line": 10,
        "kind": "unused_function",
        "symbol": "old",
    }


def _review(candidate_id: str, status: str = "confirmed_deletable") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "status": status,
        "file": "src/a.py",
        "candidate_line": 10,
        "symbol": "old",
        "kind": "unused_function",
        "removal_range": "src/a.py:10-12",
        "removable_lines": 3,
        "evidence": "No references found in allowed scope.",
        "risk": "low",
        "recommended_action": "Delete the function after tests pass.",
    }


class ValidateReviewsTests(unittest.TestCase):
    def test_complete_reviews_pass_with_summary(self) -> None:
        result = validate_reviews.validate(
            {"candidates": [_candidate("DC000001"), _candidate("DC000002")]},
            [{"chunk_id": "CHUNK_001", "results": [_review("DC000001"), _review("DC000002", "false_positive")]}],
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"]["review_status"], "COMPLETE")
        self.assertEqual(result["summary"]["confirmed_deletable"], 1)
        self.assertEqual(result["summary"]["false_positive"], 1)
        self.assertEqual(result["summary"]["total_removable_lines"], 3)

    def test_missing_candidate_fails(self) -> None:
        result = validate_reviews.validate(
            {"candidates": [_candidate("DC000001"), _candidate("DC000002")]},
            [{"chunk_id": "CHUNK_001", "results": [_review("DC000001")]}],
        )

        self.assertFalse(result["valid"])
        self.assertIn("Missing review for candidate DC000002", result["errors"])

    def test_missing_required_field_fails(self) -> None:
        review = _review("DC000001")
        del review["removable_lines"]

        result = validate_reviews.validate(
            {"candidates": [_candidate("DC000001")]},
            [{"chunk_id": "CHUNK_001", "results": [review]}],
        )

        self.assertFalse(result["valid"])
        self.assertIn("Review DC000001 missing required field removable_lines", result["errors"])

    def test_plan_membership_violation_fails(self) -> None:
        result = validate_reviews.validate(
            {"candidates": [_candidate("DC000001"), _candidate("DC000002")]},
            [{"chunk_id": "CHUNK_001", "results": [_review("DC000001"), _review("DC000002")]}],
            plan={
                "chunks": [
                    {
                        "chunk_id": "CHUNK_001",
                        "candidate_ids": ["DC000001"],
                    },
                    {
                        "chunk_id": "CHUNK_002",
                        "candidate_ids": ["DC000002"],
                    },
                ]
            },
        )

        self.assertFalse(result["valid"])
        self.assertIn(
            "Review DC000002 is not assigned to chunk CHUNK_001",
            result["errors"],
        )

    def test_cli_writes_validation_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            review_path = root / "review.json"
            output_path = root / "validation.json"
            candidates_path.write_text(
                json.dumps({"candidates": [_candidate("DC000001")]}),
                encoding="utf-8",
            )
            review_path.write_text(
                json.dumps({"chunk_id": "CHUNK_001", "results": [_review("DC000001")]}),
                encoding="utf-8",
            )

            result = validate_reviews.main(
                [str(candidates_path), str(review_path), "--out", str(output_path)]
            )

            self.assertEqual(result, 0)
            self.assertTrue(json.loads(output_path.read_text(encoding="utf-8"))["valid"])


if __name__ == "__main__":
    unittest.main()
