"""Guard the staged declarative model-verification boundary."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "model_verify_declarative.py"
SIMPLE_BOX = ROOT / "examples" / "simple-box" / "verification"
LEGACY_MODEL = ROOT / "examples" / "bracket" / "verification" / "verify_model.py"


class DeclarativeModelVerificationBoundaryTests(unittest.TestCase):
    """Keep Forge as producer/data owner rather than CAD checker owner."""

    def test_simple_box_is_declarative(self):
        """The first migrated model contains data, not a procedural verifier."""

        self.assertTrue((SIMPLE_BOX / "verify.py").is_file())
        self.assertFalse((SIMPLE_BOX / "verify_model.py").exists())
        self.assertTrue((SIMPLE_BOX / "change_length.json").is_file())

    def test_unmigrated_model_keeps_legacy_path(self):
        """The one-model proof may not mechanically migrate the catalog."""

        self.assertTrue(LEGACY_MODEL.is_file())
        simple_ci = (
            ROOT / "examples" / "simple-box" / "ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/model_verify_declarative.py", simple_ci)
        self.assertNotIn("scripts/model_verify.py", simple_ci)

    def test_shared_launcher_only_produces_and_hands_off(self):
        """Forge launcher may replay Forge output but not check SolidCraft data."""

        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("run_document", text)
        self.assertIn("run_solidcraft_verification", text)

        forbidden_checker_knowledge = (
            '"solidcraft-cli"',
            "'solidcraft-cli'",
            '"body_count"',
            "'body_count'",
            '"bbox"',
            "'bbox'",
            '"timeline"',
            "'timeline'",
            '"params"',
            "'params'",
        )
        for value in forbidden_checker_knowledge:
            with self.subTest(value=value):
                self.assertNotIn(value, text)

    def test_simple_box_verify_contains_no_checker_implementation(self):
        """The model verification file contains only model-specific verification data."""

        text = (SIMPLE_BOX / "verify.py").read_text(encoding="utf-8")
        forbidden = (
            "argparse",
            "run_command",
            "run_document",
            "VerificationCheck",
            "VerificationContext",
            "solidcraft-cli",
            "model.yml",
            "import yaml",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
