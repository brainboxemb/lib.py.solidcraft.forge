"""Keep the verification library separate from the CAD runtime image."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ROOT_CI = ROOT / "cad-ci.yml"
VERIFICATION_CI = ROOT / "verification" / "library" / "ci.yml"
VERIFICATION_REQUIREMENTS = (
    ROOT / "verification" / "library" / "requirements.txt"
)
REFERENCE_CI = ROOT / "verification" / "references" / "ci.yml"
MODEL_VERIFY = ROOT / "scripts" / "model_verify.py"
REFERENCE_VERIFY = ROOT / "scripts" / "verification_evidence.py"

VERIFICATION_COMMIT = "b5e68133f7a119eb8b876a3c0628cc1963bd09a2"


class VerificationLibraryDependencyTests(unittest.TestCase):
    """Prove the released verification package is one reusable CI dependency."""

    def test_root_ci_declares_verification_library_item(self):
        text = ROOT_CI.read_text(encoding="utf-8")
        self.assertIn("  - verification/library", text)

    def test_verification_item_builds_exact_released_commit(self):
        self.assertTrue(VERIFICATION_CI.is_file())
        requirements = VERIFICATION_REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn(VERIFICATION_COMMIT, requirements)

    def test_every_model_depends_on_verification_library(self):
        model_ci_files = sorted((ROOT / "examples").glob("*/ci.yml"))
        self.assertTrue(model_ci_files)
        for path in model_ci_files:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn("  - verification-library", text)

    def test_reference_verification_depends_on_verification_library(self):
        text = REFERENCE_CI.read_text(encoding="utf-8")
        self.assertIn("  - verification-library", text)

    def test_runtime_consumers_mount_the_separate_verification_wheel(self):
        model_text = MODEL_VERIFY.read_text(encoding="utf-8")
        reference_text = REFERENCE_VERIFY.read_text(encoding="utf-8")
        for text in (model_text, reference_text):
            self.assertIn('"verification-library"', text)
            self.assertIn("cad_verification", text)


if __name__ == "__main__":
    unittest.main()
