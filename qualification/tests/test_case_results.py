"""Structured results must use case-specific Q1/Q2 evidence."""

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from qualification import results


CASE = {
    "slug": "case-one",
    "title": "Case one",
    "mutation": "No saved-design mutation required for this focused test.",
}


def _write_tsv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


class CaseSpecificResultTests(unittest.TestCase):
    def _collect(self, qualification_dir, native_root):
        with patch.object(results, "QUALIFICATION_CASES", [CASE]):
            return results.collect(
                qualification_dir,
                native_root,
                "abc123",
                "0.test",
                "0.42.0",
                "2026-11-17T00:00:00Z",
            )

    def test_global_suite_success_does_not_create_case_q1_q2_pass(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            qualification_dir = root / "qualification"
            native_root = root / "native"
            qualification_dir.mkdir()
            (qualification_dir / "q1-python-tests.txt").write_text(
                "OK\n",
                encoding="utf-8",
            )
            (qualification_dir / "q2-python-qualification-tests.txt").write_text(
                "OK\n",
                encoding="utf-8",
            )
            _write_tsv(
                qualification_dir / "q2-command-contract.tsv",
                ("case", "commands", "status"),
                [{"case": "case-one", "commands": "3", "status": "PASS"}],
            )

            case = self._collect(qualification_dir, native_root)["cases"]["case-one"]
            self.assertEqual(case["levels"]["q1"]["status"], "missing")
            self.assertEqual(case["levels"]["q2"]["status"], "missing")
            self.assertEqual(case["status"], "incomplete")

    def test_pass_row_without_test_targets_is_still_missing(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            qualification_dir = root / "qualification"
            native_root = root / "native"
            q1_log = qualification_dir / "case-evidence" / "q1" / "case-one.txt"
            q1_log.parent.mkdir(parents=True)
            q1_log.write_text("Q1 target PASS\n", encoding="utf-8")
            _write_tsv(
                qualification_dir / "q1-case-evidence.tsv",
                ("case", "status", "tests", "evidence"),
                [{
                    "case": "case-one",
                    "status": "PASS",
                    "tests": "[]",
                    "evidence": "case-evidence/q1/case-one.txt",
                }],
            )

            case = self._collect(
                qualification_dir,
                native_root,
            )["cases"]["case-one"]
            self.assertEqual(case["levels"]["q1"]["status"], "missing")

    def test_case_pass_requires_target_list_and_run_log(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            qualification_dir = root / "qualification"
            native_root = root / "native"
            q1_log = qualification_dir / "case-evidence" / "q1" / "case-one.txt"
            q2_log = qualification_dir / "case-evidence" / "q2" / "case-one.txt"
            q1_log.parent.mkdir(parents=True)
            q2_log.parent.mkdir(parents=True)
            q1_log.write_text("Q1 target PASS\n", encoding="utf-8")
            q2_log.write_text("Q2 target PASS\n", encoding="utf-8")
            q1_targets = [{"file": "scpf/tests/test_api.py", "test": "test_api"}]
            q2_targets = [
                {
                    "file": "examples/case-one/tests/test_contract.py",
                    "test": "test_contract",
                }
            ]
            _write_tsv(
                qualification_dir / "q1-case-evidence.tsv",
                ("case", "status", "tests", "evidence"),
                [{
                    "case": "case-one",
                    "status": "PASS",
                    "tests": json.dumps(q1_targets),
                    "evidence": "case-evidence/q1/case-one.txt",
                }],
            )
            _write_tsv(
                qualification_dir / "q2-case-evidence.tsv",
                ("case", "status", "tests", "evidence"),
                [{
                    "case": "case-one",
                    "status": "PASS",
                    "tests": json.dumps(q2_targets),
                    "evidence": "case-evidence/q2/case-one.txt",
                }],
            )
            _write_tsv(
                qualification_dir / "q2-command-contract.tsv",
                ("case", "commands", "status"),
                [{"case": "case-one", "commands": "3", "status": "PASS"}],
            )

            case = self._collect(qualification_dir, native_root)["cases"]["case-one"]
            self.assertEqual(case["levels"]["q1"]["status"], "pass")
            self.assertEqual(case["levels"]["q2"]["status"], "pass")
            self.assertEqual(case["levels"]["q1"]["tests"], q1_targets)
            self.assertEqual(case["levels"]["q2"]["tests"], q2_targets)
            self.assertEqual(
                case["levels"]["q1"]["evidence"],
                ["q1-case-evidence.txt"],
            )
            self.assertEqual(
                case["levels"]["q2"]["evidence"],
                ["q2-case-evidence.txt"],
            )
            self.assertTrue(
                (native_root / "case-one" / "q1-case-evidence.txt").is_file()
            )
            self.assertTrue(
                (native_root / "case-one" / "q2-case-evidence.txt").is_file()
            )


if __name__ == "__main__":
    unittest.main()
