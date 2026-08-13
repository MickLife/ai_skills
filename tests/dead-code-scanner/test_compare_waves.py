from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "skills" / "dead-code-scanner"
sys.path.insert(0, str(ROOT / "scripts"))

import compare_waves  # noqa: E402


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


class CompareWavesTests(unittest.TestCase):
    def test_compare_identifies_new_resolved_and_carried_over(self) -> None:
        previous = {
            "candidates": [
                _candidate("DC000001", "src/a.py", "old_a"),
                _candidate("DC000002", "src/b.py", "old_b"),
            ]
        }
        current = {
            "candidates": [
                _candidate("DC000001", "src/a.py", "old_a"),
                _candidate("DC000002", "src/c.py", "new_c"),
            ]
        }

        result = compare_waves.compare(previous, current)

        self.assertEqual([item["symbol"] for item in result["carried_over"]], ["old_a"])
        self.assertEqual([item["symbol"] for item in result["resolved"]], ["old_b"])
        self.assertEqual([item["symbol"] for item in result["new"]], ["new_c"])

    def test_cli_writes_comparison_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_path = root / "previous.json"
            current_path = root / "current.json"
            output_path = root / "diff.json"
            previous_path.write_text(
                json.dumps({"candidates": [_candidate("DC000001", "src/a.py", "old")]}),
                encoding="utf-8",
            )
            current_path.write_text(
                json.dumps({"candidates": [_candidate("DC000001", "src/a.py", "old")]}),
                encoding="utf-8",
            )

            result = compare_waves.main(
                [str(previous_path), str(current_path), "--out", str(output_path)]
            )

            self.assertEqual(result, 0)
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["carried_over"], 1)


if __name__ == "__main__":
    unittest.main()
