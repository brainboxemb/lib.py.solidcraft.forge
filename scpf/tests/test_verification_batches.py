"""Guard Forge-owned CAD runtime batching without changing item ownership."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
MODEL_BATCH = ROOT / "scripts" / "model_verification_batch.py"
REFERENCE_BATCH = ROOT / "scripts" / "reference_verification_batch.py"
REFERENCE_VALIDATION = ROOT / "verification" / "reference_validation.py"
BUILD123D_EXPORT = ROOT / "verification" / "build123d_export.py"


class VerificationBatchContractTests(unittest.TestCase):
    """Keep logical case items separate from expensive runtime startup."""

    def test_existing_case_templates_depend_on_batch_items(self):
        text = CAD_CI.read_text(encoding="utf-8")
        self.assertIn("- model-verification-batch", text)
        self.assertIn("- reference-verification-batch", text)
        self.assertIn(
            "scripts/model_verification_batch.py, materialize",
            text,
        )
        self.assertIn(
            "scripts/reference_verification_batch.py, materialize",
            text,
        )

    def test_reference_batch_groups_all_four_engines(self):
        text = REFERENCE_VALIDATION.read_text(encoding="utf-8")
        self.assertIn(
            'IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")',
            text,
        )
        self.assertIn("for implementation in implementations:", text)
        self.assertIn("for slug in slugs:", text)
        self.assertIn("export_build123d_batch", text)

    def test_build123d_batch_imports_once_and_continues_cases(self):
        text = BUILD123D_EXPORT.read_text(encoding="utf-8")
        self.assertEqual(text.count("from build123d import export_stl"), 1)
        self.assertIn("for row in rows:", text)
        self.assertIn("continue so every case gets a result", text)
        self.assertIn("return 1 if failed else 0", text)

    def test_model_batch_keeps_case_output_separate(self):
        text = MODEL_BATCH.read_text(encoding="utf-8")
        self.assertIn("for slug in processed_declarative_slugs()", text)
        self.assertIn('"output": f"/output/models/{slug}/model_verify"', text)
        self.assertIn("for row in rows:", text)
        self.assertIn("materialize_case", text)

    def test_reference_batch_materializes_only_current_child(self):
        text = REFERENCE_BATCH.read_text(encoding="utf-8")
        self.assertIn("reference_identity()", text)
        self.assertIn("case_destination", text)
        self.assertIn("implementation_row", text)


if __name__ == "__main__":
    unittest.main()
