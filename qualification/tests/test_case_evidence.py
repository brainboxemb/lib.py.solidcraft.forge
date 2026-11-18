"""Qualification case-specific Q1/Q2 evidence metadata."""

from pathlib import Path
import unittest

from qualification.case_evidence import CASE_EVIDENCE, validate_case_evidence
from qualification.cases import supported_qualification_cases
from qualification.run_case_evidence import ROOT, _target_cwd, _target_env


class CaseEvidenceMetadataTests(unittest.TestCase):
    def test_every_supported_case_has_real_q1_and_q2_targets(self):
        validate_case_evidence()
        expected = {
            case["slug"]
            for case in supported_qualification_cases()
        }
        self.assertEqual(set(CASE_EVIDENCE), expected)

    def test_case_runner_preserves_q1_isolation_and_runs_q2_from_repo(self):
        outside = Path("/tmp/outside-repo")
        self.assertEqual(
            _target_cwd(
                {"file": "scpf/tests/test_geometry_features.py"},
                caller_cwd=outside,
            ),
            outside,
        )
        self.assertEqual(
            _target_cwd(
                {"file": "examples/simple-box/tests/test_contract.py"},
                caller_cwd=outside,
            ),
            ROOT,
        )

    def test_case_runner_uses_current_checkout_for_imports(self):
        env = _target_env()
        paths = env["PYTHONPATH"].split(":")
        self.assertEqual(paths[0], str(ROOT / "scpf"))
        self.assertEqual(paths[1], str(ROOT))

    def test_q1_and_q2_use_separate_test_layers(self):
        for slug, levels in CASE_EVIDENCE.items():
            with self.subTest(case=slug):
                self.assertTrue(levels["q1"])
                self.assertTrue(levels["q2"])
                self.assertTrue(
                    all(
                        row["file"].startswith("scpf/tests/")
                        for row in levels["q1"]
                    )
                )
                self.assertTrue(
                    all(
                        row["file"].startswith(f"examples/{slug}/tests/")
                        for row in levels["q2"]
                    )
                )


if __name__ == "__main__":
    unittest.main()
