from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
PARTIAL = ROOT / "site/layouts/partials/cad/development-warning.html"


class DevelopmentWarningTests(unittest.TestCase):
    def test_warning_has_one_shared_forge_owned_source(self):
        text = PARTIAL.read_text(encoding="utf-8")
        self.assertIn("data-forge-development-warning", text)
        self.assertIn("Development version.", text)
        self.assertIn("under active development and testing", text)
        self.assertIn("not a support guarantee", text)
        self.assertIn("production-readiness claim", text)

    def test_every_custom_route_entry_uses_shared_partial(self):
        for relative in (
            "site/layouts/home.html",
            "site/layouts/models/list.html",
            "site/layouts/models/single.html",
            "site/layouts/_partials/custom/page-begin.html",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(
                'partial "cad/development-warning.html"',
                source,
                relative,
            )
            self.assertNotIn("Forge is under active development and testing", source)

    def test_warning_is_visibly_red_and_high_contrast(self):
        css = (ROOT / "site/assets/css/custom.css").read_text(encoding="utf-8")
        self.assertIn(".forge-development-warning", css)
        self.assertIn("background:#a92525", css)
        self.assertIn("color:#fff", css)


if __name__ == "__main__":
    unittest.main()
