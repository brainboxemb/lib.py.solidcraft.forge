"""Case-specific Q1/Q2 evidence metadata."""
import unittest
from qualification.case_evidence import CASE_EVIDENCE, validate_case_evidence
from qualification.cases import supported_qualification_cases
class CaseEvidenceMetadataTests(unittest.TestCase):
    def test_every_supported_case_has_real_q1_and_q2_targets(self):
        validate_case_evidence(); self.assertEqual(set(CASE_EVIDENCE),{c["slug"] for c in supported_qualification_cases()})
    def test_q1_and_q2_use_separate_test_layers(self):
        for slug,levels in CASE_EVIDENCE.items():
            with self.subTest(case=slug):
                self.assertTrue(all(r["file"].startswith("scpf/tests/") for r in levels["q1"]))
                self.assertTrue(all(r["file"].startswith("qualification/tests/") for r in levels["q2"]))
if __name__=="__main__": unittest.main()
