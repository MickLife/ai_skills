from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "skills" / "dead-code-scanner"
sys.path.insert(0, str(ROOT / "scripts"))

import compare_waves  # noqa: E402
import plan_review  # noqa: E402
import validate_reviews  # noqa: E402


def _candidate(candidate_id: str, file: str, symbol: str) -> dict[str, object]:
    return {
        "id": candidate_id,
        "tool": "vulture",
        "file": file,
        "line": 10,
        "kind": "unused_function",
        "symbol": symbol,
        "message": f"unused function '{symbol}'",
    }


def _review(candidate_id: str, chunk_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "status": "confirmed_deletable",
        "file": "src/a.py",
        "candidate_line": 10,
        "symbol": "old",
        "kind": "unused_function",
        "removal_range": "src/a.py:10-12",
        "removable_lines": 3,
        "evidence": "Local references checked.",
        "risk": "low",
        "recommended_action": "Delete after tests pass.",
        "chunk_id": chunk_id,
    }


class WorkflowTests(unittest.TestCase):
    def test_review_plan_validation_and_wave_compare_work_together(self) -> None:
        wave0 = {
            "target": "src",
            "candidates": [_candidate("DC000001", "src/a.py", "old")],
        }
        plan = plan_review.build_plan(wave0, chunk_size=25, source_path="wave0.json")
        review = {
            "chunk_id": plan["chunks"][0]["chunk_id"],
            "results": [_review("DC000001", plan["chunks"][0]["chunk_id"])],
        }

        validation = validate_reviews.validate(wave0, [review], plan=plan)
        self.assertTrue(validation["valid"])

        wave1 = {
            "target": "src",
            "candidates": [_candidate("DC000001", "src/b.py", "new_after_delete")],
        }
        diff = compare_waves.compare(wave0, wave1)

        self.assertEqual(diff["summary"]["resolved"], 1)
        self.assertEqual(diff["summary"]["new"], 1)
        self.assertEqual(diff["summary"]["carried_over"], 0)


if __name__ == "__main__":
    unittest.main()
