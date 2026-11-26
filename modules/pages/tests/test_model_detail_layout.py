from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
LAYOUT = ROOT / "site/layouts/models/single.html"


class ModelDetailLayoutTests(unittest.TestCase):
    def test_verification_and_example_headings_are_distinct(self):
        text = LAYOUT.read_text(encoding="utf-8")
        self.assertIn("What this verifies", text)
        self.assertIn("What this model makes", text)

    def test_engineering_explanation_follows_primary_source(self):
        text = LAYOUT.read_text(encoding="utf-8")
        source = text.index('id="primary-source"')
        explanation = text.index('id="engineering-explanation"')
        commands = text.index('cad-command-section')
        self.assertLess(source, explanation)
        self.assertLess(explanation, commands)

    def test_verification_checks_are_collapsed_by_default(self):
        text = LAYOUT.read_text(encoding="utf-8")
        marker = '<details class="cad-panel cad-collapsible" id="check-overview">'
        self.assertIn(marker, text)
        block = text[text.index(marker):text.index(marker) + 500]
        self.assertNotIn(" open", block)
        self.assertIn("cad-collapsible-title", block)
        self.assertIn("cad-collapsible-body", block)


if __name__ == "__main__":
    unittest.main()
