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

    def test_staged_outputs_restore_schema_v4_case_result(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            qualification_dir = root / "qualification"
            native_root = root / "native"
            stages_root = root / "stages"
            case_dir = native_root / "case-one"
            case_dir.mkdir(parents=True)
            qualification_dir.mkdir()

            for level in ("q1", "q2"):
                evidence = (
                    qualification_dir
                    / "case-evidence"
                    / level
                    / "case-one.txt"
                )
                evidence.parent.mkdir(parents=True, exist_ok=True)
                evidence.write_text(f"{level.upper()} PASS\n", encoding="utf-8")

            for index, stage in enumerate(
                ("q1", "q2", "compile", "replay", "evaluate"),
                start=1,
            ):
                path = stages_root / "case-one" / f"{index:02d}-{stage}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps({"status": "pass"}),
                    encoding="utf-8",
                )

            (root / "case-one.json").write_text(
                json.dumps({"commands": [{"command": "solid.box"}]}),
                encoding="utf-8",
            )
            for name in ("model.sc", "model.step", "results.json", "measurements.json"):
                (case_dir / name).write_text("{}", encoding="utf-8")
            (case_dir / "validation.json").write_text(
                json.dumps({"q4": "pass", "q5": "not-required"}),
                encoding="utf-8",
            )
            (case_dir / "visual-validation.json").write_text(
                json.dumps({
                    "status": "pass",
                    "regression": {"status": "pass"},
                    "expected_shape": {
                        "status": "pass",
                        "required_views": ["front"],
                    },
                }),
                encoding="utf-8",
            )
            (case_dir / "model-front.png").write_bytes(b"png")

            _write_tsv(
                qualification_dir / "native-validation.tsv",
                ("case", "q4", "q5"),
                [{"case": "case-one", "q4": "PASS", "q5": "NOT-REQUIRED"}],
            )
            _write_tsv(
                qualification_dir / "visual-validation.tsv",
                ("case", "status"),
                [{"case": "case-one", "status": "PASS"}],
            )

            targets = {
                "q1": [{"file": "scpf/tests/test_api.py", "test": "test_api"}],
                "q2": [{"file": "examples/case-one/tests/test_contract.py", "test": "test_contract"}],
            }
            with patch.object(results, "QUALIFICATION_CASES", [CASE]), \
                 patch.object(results, "evidence_for", side_effect=lambda slug, level: targets[level]):
                aggregate = results.collect(
                    qualification_dir,
                    native_root,
                    "abc123",
                    "0.test",
                    "0.42.0",
                    "2026-11-18T00:00:00Z",
                    output_root=root,
                    stages_root=stages_root,
                    cases=("case-one",),
                )

            case = aggregate["cases"]["case-one"]
            self.assertEqual(case["schema_version"], 4)
            self.assertEqual(case["status"], "pass")
            self.assertEqual(
                [case["levels"][f"q{index}"]["status"] for index in range(1, 7)],
                ["pass", "pass", "pass", "pass", "not-required", "pass"],
            )
            persisted = json.loads(
                (case_dir / "qualification-result.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(persisted["levels"]["q6"]["status"], "pass")

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
