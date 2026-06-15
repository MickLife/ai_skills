from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scan  # noqa: E402


class ScanTests(unittest.TestCase):
    def test_scan_assigns_stable_candidate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "pkg"
            target.mkdir()
            out = root / "report.json"

            def fake_run(cmd: list[str], **kwargs: object) -> object:
                if "vulture" in cmd:
                    return mock.Mock(
                        stdout=(
                            "pkg/a.py:3: unused variable 'alpha' (100% confidence)\n"
                            "pkg/b.py:9: unused function 'beta' (80% confidence)\n"
                        )
                    )
                return mock.Mock(stdout="[]")

            with mock.patch.object(scan, "_module_missing", return_value=False):
                with mock.patch.object(scan.subprocess, "run", side_effect=fake_run):
                    result = scan.main([str(target), "--out", str(out)])

            self.assertEqual(result, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(
                [candidate["id"] for candidate in data["candidates"]],
                ["DC000001", "DC000002"],
            )

    def test_whitelist_marks_candidates_without_suppressing_vulture_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "pkg"
            target.mkdir()
            whitelist = root / "whitelist.py"
            whitelist.write_text("delete\n", encoding="utf-8")
            out = root / "report.json"
            commands: list[list[str]] = []

            def fake_run(cmd: list[str], **kwargs: object) -> object:
                commands.append(cmd)
                if "vulture" in cmd:
                    return mock.Mock(
                        stdout="pkg/mod.py:3: unused variable 'delete' (100% confidence)\n"
                    )
                return mock.Mock(stdout="[]")

            with mock.patch.object(scan, "_module_missing", return_value=False):
                with mock.patch.object(scan.subprocess, "run", side_effect=fake_run):
                    result = scan.main(
                        [
                            str(target),
                            "--whitelist",
                            str(whitelist),
                            "--out",
                            str(out),
                        ]
                    )

            self.assertEqual(result, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["total"], 1)
            self.assertTrue(data["candidates"][0]["in_whitelist"])

            vulture_cmd = next(cmd for cmd in commands if "vulture" in cmd)
            self.assertNotIn(str(whitelist), vulture_cmd)


if __name__ == "__main__":
    unittest.main()
