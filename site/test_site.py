#!/usr/bin/env python3
"""Test the current example-driven Forge documentation source."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteSourceTests(unittest.TestCase):
    def test_site_orchestrator_keeps_html_in_explicit_render_layer(self):
        build = (SITE / "build.py").read_text(encoding="utf-8")
        guides = (SITE / "guides.py").read_text(encoding="utf-8")

        for token in (
            "from qualification.",
            "import qualification.",
            "EXAMPLES =",
            "SCHEMATICS =",
            "COPY_SCRIPT =",
            "SEARCH_SCRIPT =",
        ):
            self.assertNotIn(token, build)

        for markup in (
            "<!doctype html",
            "<main",
            "<section",
            "<article",
            "<table",
            "<li",
            "<a ",
        ):
            self.assertNotIn(markup, build.lower())
        self.assertIn("from html_writer import", build)
        self.assertNotIn("GUIDES = [", guides)
        self.assertNotIn("<h2", guides)

        self.assertTrue((SITE / "html_writer.py").is_file())
        self.assertTrue((SITE / "templates" / "page.html").is_file())
        self.assertTrue((SITE / "templates" / "guide-overview.html").is_file())
        self.assertTrue((SITE / "templates" / "example.html").is_file())
        self.assertTrue((SITE / "templates" / "home.html").is_file())
        self.assertTrue((SITE / "templates" / "api-design-contract.html").is_file())
        self.assertTrue((SITE / "templates" / "reference-overview.html").is_file())
        self.assertTrue((SITE / "templates" / "cheatsheet-item.html").is_file())
        self.assertTrue((SITE / "templates" / "cheatsheet-section.html").is_file())
        self.assertTrue((SITE / "static" / "copy.js").is_file())
        self.assertTrue((SITE / "static" / "search.js").is_file())
        self.assertTrue((SITE / "content" / "guides.json").is_file())

    def test_source_only_site_build_discovers_all_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "site"
            subprocess.run(
                [
                    sys.executable,
                    str(SITE / "build.py"),
                    "--out",
                    str(out),
                    "--source-sha",
                    "source-test",
                ],
                cwd=ROOT,
                check=True,
            )

            manifest = json.loads(
                (out / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["examples"]), 32)

            qualification = json.loads(
                (out / "qualification" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(qualification["cases"]), 32)
            self.assertEqual(
                qualification["evidence_source"],
                "build/main",
            )

            simple_case = qualification["cases"]["simple-box"]
            self.assertEqual(
                simple_case["documentation_source"],
                "examples/simple-box/README.md",
            )

            for slug in manifest["examples"]:
                with self.subTest(slug=slug):
                    self.assertTrue(
                        (out / "examples" / slug / "index.html").is_file()
                    )
                    self.assertTrue(
                        (
                            out
                            / "qualification"
                            / slug
                            / "index.html"
                        ).is_file()
                    )

            simple_page = (
                out / "examples" / "simple-box" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "Establish the smallest model/parameter contract",
                simple_page,
            )
            self.assertIn(
                "parameters.add for the public dimensions",
                simple_page,
            )
            self.assertIn(
                "cube([40,30,10]) is the constructive-geometry baseline",
                simple_page,
            )
            self.assertIn(
                "Its body size fully describes the visible geometry",
                simple_page,
            )

            home = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("static/copy.js", home)
            self.assertIn("static/search.js", home)
            self.assertNotIn("<script>(() =>", home)

            search = json.loads(
                (out / "search-index.json").read_text(encoding="utf-8")
            )
            example_entries = [
                row for row in search["entries"]
                if row["kind"] == "Example"
            ]
            self.assertEqual(len(example_entries), 32)


if __name__ == "__main__":
    unittest.main()
