from pathlib import Path
import unittest


class CatalogLandingCopyTests(unittest.TestCase):
    def test_examples_and_verification_are_user_facing(self):
        root = Path(__file__).resolve().parents[3]
        examples = (root / "site/content/examples/_index.md").read_text(
            encoding="utf-8"
        )
        verification = (
            root / "site/content/verification/_index.md"
        ).read_text(encoding="utf-8")

        self.assertIn("small, practical Forge/SCPF models", examples)
        self.assertIn("generated/native result", examples)
        self.assertNotIn("model.yml.purpose", examples)
        self.assertNotIn("physical model owners", examples)

        self.assertIn("used to qualify Forge/SCPF behaviour", verification)
        self.assertIn(
            "not a support or production-readiness guarantee",
            verification,
        )
        self.assertNotIn("model.yml.purpose", verification)
        self.assertNotIn("physical owner", verification)


if __name__ == "__main__":
    unittest.main()
