"""Guard the staged declarative model-verification boundary."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "model_verify_declarative.py"

MIGRATED_MODELS = (
    "simple-box",
    "anchor-topology-mutation",
    "assembly-owned-anchor",
    "attach-angle",
    "corner-anchor",
    "eight-corner-brackets",
    "four-corner-l",
    "parametric-anchor",
    "parametric-attach",
    "parametric-offset",
    "xz-anchor",
)

LEGACY_MODEL = "bracket"

FORBIDDEN_VERIFY_IMPLEMENTATION = (
    "argparse",
    "run_command",
    "run_document",
    "VerificationCheck",
    "VerificationContext",
    "solidcraft-cli",
    "model.yml",
    "import yaml",
)


class DeclarativeModelVerificationBoundaryTests(unittest.TestCase):
    """Keep Forge as producer/data owner rather than CAD checker owner."""

    def test_migrated_models_use_verify_data_only(self):
        """Every migrated model uses verify.py and the shared launcher."""

        for slug in MIGRATED_MODELS:
            with self.subTest(slug=slug):
                verification = ROOT / "examples" / slug / "verification"
                self.assertTrue((verification / "verify.py").is_file())
                self.assertFalse((verification / "verify_model.py").exists())

                ci = (
                    ROOT / "examples" / slug / "ci.yml"
                ).read_text(encoding="utf-8")
                if "template: forge-model-declarative" in ci:
                    root_ci = (ROOT / "cad-ci.yml").read_text(encoding="utf-8")
                    self.assertIn(
                        "scripts/model_verify_declarative.py",
                        root_ci,
                    )
                    self.assertNotIn("scripts/model_verify.py", root_ci)
                else:
                    self.assertIn("scripts/model_verify_declarative.py", ci)
                    self.assertNotIn("scripts/model_verify.py", ci)

                text = (verification / "verify.py").read_text(
                    encoding="utf-8"
                )
                for value in FORBIDDEN_VERIFY_IMPLEMENTATION:
                    self.assertNotIn(value, text)

    def test_simple_box_keeps_its_model_specific_mutation(self):
        """The representative model keeps its own mutation command data."""

        verification = ROOT / "examples" / "simple-box" / "verification"
        self.assertTrue((verification / "change_length.json").is_file())

    def test_excluded_model_keeps_legacy_path(self):
        """The batch may not mechanically migrate an excluded model."""

        verification = ROOT / "examples" / LEGACY_MODEL / "verification"
        self.assertTrue((verification / "verify_model.py").is_file())
        self.assertFalse((verification / "verify.py").exists())

        ci = (
            ROOT / "examples" / LEGACY_MODEL / "ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/model_verify.py", ci)
        self.assertNotIn("scripts/model_verify_declarative.py", ci)

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


if __name__ == "__main__":
    unittest.main()
