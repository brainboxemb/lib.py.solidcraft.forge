from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from cad_library_pages.cheatsheet import prepare_cheatsheet
from cad_library_pages.guides import prepare_guides


class AuthoredDocumentationProjectionTests(unittest.TestCase):
    def test_guide_and_cheatsheet_are_projected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            guide = root / "docs/guide"
            guide.mkdir(parents=True)
            (guide / "index.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "guides": [
                            {
                                "slug": "getting-started",
                                "title": "Getting started",
                                "summary": "Start here.",
                                "body": "guides/getting-started.html",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (guide / "getting-started.html").write_text(
                "<h2 id=\"first\">First model</h2>\n"
                "<p>Hello <strong>world</strong> and <code>Box()</code>.</p>\n"
                "<table><thead><tr><th>Name</th><th>Meaning</th></tr></thead>"
                "<tbody><tr><td><code>x</code></td><td>Value</td></tr></tbody></table>\n",
                encoding="utf-8",
            )
            (root / "docs/cheatsheet.yml").write_text(
                "schema: 1\n"
                "groups:\n"
                "  - heading: Model classes\n"
                "    items:\n"
                "      - title: Example\n"
                "        description: Build one model.\n"
                "        snippet: Example()\n"
                "        example: simple-box\n",
                encoding="utf-8",
            )
            model = root / "models/simple-box"
            model.mkdir(parents=True)
            (model / "model.yml").write_text(
                "schema: 1\npurpose: [example, verification]\n",
                encoding="utf-8",
            )

            site = root / "site"
            prepare_guides(root, site)
            prepare_cheatsheet(root, site)

            overview = (site / "content/guide/_index.md").read_text()
            self.assertIn("[Getting started](getting-started/)", overview)
            chapter = (
                site / "content/guide/getting-started/index.md"
            ).read_text()
            self.assertIn('title: "Getting started"', chapter)
            self.assertIn("## First model", chapter)
            self.assertIn("Hello **world** and `Box()`.", chapter)
            self.assertIn("| Name | Meaning |", chapter)
            self.assertIn("| `x` | Value |", chapter)

            cheat = (site / "content/cheatsheet/_index.md").read_text()
            self.assertIn("## Model classes", cheat)
            self.assertIn("~~~python", cheat)
            self.assertIn("../examples/simple-box/", cheat)


if __name__ == "__main__":
    unittest.main()
