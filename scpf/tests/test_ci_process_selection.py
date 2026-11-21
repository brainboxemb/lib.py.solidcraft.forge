"""Guard current Verification model processing."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


class CiProcessSelectionContractTests(unittest.TestCase):
    """Keep every current full Verification model visible to CAD-CI."""

    def test_all_verification_models_are_processed(self):
        """Match processed model items to distributed model.yml membership."""

        configured = {}
        for ci_path in sorted(EXAMPLES.glob("*/ci.yml")):
            text = ci_path.read_text(encoding="utf-8")
            match = re.search(
                r"^process:\s*(true|false)\s*$",
                text,
                re.MULTILINE,
            )
            self.assertIsNotNone(
                match,
                f"missing explicit process declaration: {ci_path}",
            )
            configured[ci_path.parent.name] = match.group(1) == "true"

        expected = {
            path.parent.name
            for path in EXAMPLES.glob("*/model.yml")
        }
        self.assertEqual(set(configured), expected)
        self.assertEqual(
            {slug for slug, enabled in configured.items() if enabled},
            expected,
        )
        self.assertFalse(
            {slug for slug, enabled in configured.items() if not enabled},
        )


if __name__ == "__main__":
    unittest.main()
