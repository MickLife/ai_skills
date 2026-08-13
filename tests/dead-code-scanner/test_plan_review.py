from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "skills" / "dead-code-scanner"
sys.path.insert(0, str(ROOT / "scripts"))

import plan_review  # noqa: E402


def _candidate(candidate_id: str, file: str) -> dict[str, object]:
    return {
        "id": candidate_id,
        "tool": "vulture",
        "file": file,
        "line": 1,
        "kind": "unused_function",
        "symbol": candidate_id.lower(),
        "message": "unused",
        "confidence": 100,
        "rule": None,
        "in_whitelist": False,
    }


class PlanReviewTests(unittest.TestCase):
    def test_groups_candidates_by_file_and_splits_large_files(self) -> None:
        candidates = [
            _candidate("DC000001", "src/a.py"),
            _candidate("DC000002", "src/a.py"),
            _candidate("DC000003", "src/a.py"),
            _candidate("DC000004", "src/b.py"),
        ]

        plan = plan_review.build_plan(
            {"target": "src", "candidates": candidates},
            chunk_size=2,
            source_path="candidates.json",
        )

        self.assertEqual(plan["candidate_file"], "candidates.json")
        self.assertEqual(plan["total_candidates"], 4)
        self.assertEqual(plan["chunk_size"], 2)
        self.assertEqual(len(plan["chunks"]), 3)
        self.assertEqual(plan["chunks"][0]["candidate_ids"], ["DC000001", "DC000002"])
        self.assertEqual(plan["chunks"][1]["candidate_ids"], ["DC000003"])
        self.assertEqual(plan["chunks"][2]["candidate_ids"], ["DC000004"])
        self.assertEqual(plan["chunks"][0]["allowed_paths"], ["src/a.py"])

        planned_ids = [
            candidate_id
            for chunk in plan["chunks"]
            for candidate_id in chunk["candidate_ids"]
        ]
        self.assertEqual(planned_ids, [candidate["id"] for candidate in candidates])

    def test_cli_writes_review_plan_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            output_path = root / "plan.json"
            candidates_path.write_text(
                json.dumps(
                    {"target": "src", "candidates": [_candidate("DC000001", "src/a.py")]},
                ),
                encoding="utf-8",
            )

            result = plan_review.main(
                [str(candidates_path), "--chunk-size", "10", "--out", str(output_path)]
            )

            self.assertEqual(result, 0)
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["chunks"][0]["chunk_id"], "CHUNK_001")


if __name__ == "__main__":
    unittest.main()
