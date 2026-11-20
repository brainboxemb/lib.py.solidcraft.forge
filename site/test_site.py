#!/usr/bin/env python3
"""Test the current example-driven Forge documentation source."""

from __future__ import annotations

import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from html_writer import qualification_reference_comparison


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
            "CHEATSHEET =",
            "SECTION_PRESENTATION =",
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
        self.assertTrue((SITE / "build_evidence.py").is_file())
        self.assertTrue((SITE / "qualification_view.py").is_file())
        self.assertTrue((SITE / "templates" / "page.html").is_file())
        self.assertTrue((SITE / "templates" / "guide-overview.html").is_file())
        self.assertTrue((SITE / "templates" / "example.html").is_file())
        self.assertTrue((SITE / "templates" / "home.html").is_file())
        self.assertTrue((SITE / "templates" / "api-design-contract.html").is_file())
        self.assertTrue((SITE / "templates" / "reference-overview.html").is_file())
        self.assertTrue((SITE / "templates" / "cheatsheet-item.html").is_file())
        self.assertTrue((SITE / "templates" / "cheatsheet-section.html").is_file())
        self.assertTrue((SITE / "templates" / "qualification-current.html").is_file())
        self.assertTrue((SITE / "templates" / "qualification-reference-row.html").is_file())
        self.assertTrue((SITE / "templates" / "qualification-visual-section.html").is_file())
        self.assertTrue((SITE / "templates" / "qualification-diagrams.html").is_file())
        self.assertTrue((SITE / "static" / "copy.js").is_file())
        self.assertTrue((SITE / "static" / "search.js").is_file())
        self.assertTrue((SITE / "content" / "guides.json").is_file())
        self.assertTrue((SITE / "content" / "cheatsheet.yml").is_file())
        self.assertTrue(
            (SITE / "content" / "verification-sections.yml").is_file()
        )
        self.assertTrue(
            (SITE / "templates" / "verification-group.html").is_file()
        )

    def test_verification_pages_keep_inline_source_comparison(self):
        build = (SITE / "build.py").read_text(encoding="utf-8")
        case_template = (
            SITE / "templates" / "qualification-case.html"
        ).read_text(encoding="utf-8")
        reference_template = (
            SITE / "templates" / "qualification-reference-row.html"
        ).read_text(encoding="utf-8")

        self.assertIn("${forge_source}", case_template)
        self.assertIn("${source_code}", reference_template)
        self.assertIn("qualification_reference_comparison(", build)
        self.assertIn(
            "from build_evidence import IMPLEMENTATIONS",
            build,
        )
        self.assertIn("for implementation in IMPLEMENTATIONS", build)

    def test_public_templates_use_verification_terminology(self):
        for path in (SITE / "templates").glob("*.html"):
            source = path.read_text(encoding="utf-8")
            with self.subTest(template=path.name):
                self.assertNotIn("Qualification", source)
                self.assertNotIn("/qualification/", source)

    def test_reference_source_is_rendered_beside_each_current_result(self):
        implementations = ("pythonscad", "pybosl2", "cadquery", "build123d")
        sources = {
            name: f"# unique source for {name}\nMODEL = '{name}'\n"
            for name in implementations
        }
        view = {
            "status": "pass",
            "checks": {},
            "parameters": (),
            "bodies": (),
            "verification_checks": (),
            "saved_designs": (),
            "visual_views": (),
            "site_source_commit": "site-source",
            "accepted_source_commit": "model-source",
            "build_commit": "build-commit",
            "preview_url": "preview.png",
            "commands_url": "commands.json",
            "verification_url": "verification.json",
            "measurements_url": "measurements.json",
            "native_model_url": "model.sc",
            "native_step_url": "model.step",
            "native_results_url": "results.json",
            "preview_metadata_url": "preview.json",
            "references": tuple(
                {
                    "implementation": name,
                    "status": "pass",
                    "accepted_source_commit": f"source-{name}",
                    "source_url": f"https://accepted.invalid/{name}.py",
                    "stl_url": f"https://example.invalid/{name}.stl",
                    "verification_url": f"https://example.invalid/{name}.json",
                    "preview_metadata_url": f"https://example.invalid/{name}-preview.json",
                    "preview_url": f"https://example.invalid/{name}.png",
                    "geometry_json": '{"status": "pass"}',
                }
                for name in implementations
            ),
        }

        source_urls = {
            name: f"https://current.invalid/{name}.py"
            for name in implementations
        }
        rendered = qualification_reference_comparison(
            sources,
            source_urls,
            reference_rows=view["references"],
        )

        for name in implementations:
            with self.subTest(implementation=name):
                self.assertIn(f"unique source for {name}", rendered)
                self.assertIn(f"{name}.png", rendered)
                self.assertIn(f"{name}.stl", rendered)
                self.assertIn(
                    f"https://current.invalid/{name}.py",
                    rendered,
                )
                self.assertIn(
                    f"https://accepted.invalid/{name}.py",
                    rendered,
                )

    def test_stable_site_cli_uses_only_durable_build_main_inputs(self):
        build = (SITE / "build.py").read_text(encoding="utf-8")

        self.assertIn("--build-main", build)
        self.assertIn("--build-commit", build)
        for retired in (
            "--native",
            "--diagram-root",
            "--references",
            "--evidence-sha",
            "--build-scope",
            "--build-manifest",
        ):
            self.assertNotIn(retired, build)

        workflow = (
            ROOT / ".github" / "workflows" / "scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("publish_stable_pages:", workflow)
        self.assertIn("validate_stable_pages_pr:", workflow)
        self.assertIn("cad-ci build fetch", workflow)
        self.assertIn("cad-ci build resolve", workflow)
        self.assertIn("cad-ci publish pages", workflow)
        self.assertIn(
            "generated-site/verification/manifest.json",
            workflow,
        )
        self.assertNotIn(
            "generated-site/qualification/manifest.json",
            workflow,
        )
        self.assertLess(
            workflow.index("publish_main_build:"),
            workflow.index("publish_stable_pages:"),
        )

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

            verification = json.loads(
                (out / "verification" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(verification["cases"]), 32)
            self.assertEqual(
                verification["evidence_source"],
                "build/main",
            )

            simple_case = verification["cases"]["simple-box"]
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
                            / "verification"
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

            verification_index = (
                out / "verification" / "index.html"
            ).read_text(encoding="utf-8")
            for heading in (
                "1 · Basic geometry",
                "2 · Parent/child features and faces",
                "3 · Parameters and dependencies",
                "4 · Components and occurrences",
                "5 · Anchors and local frames",
                "6 · Associative relationships",
            ):
                self.assertIn(heading, verification_index)
            self.assertLess(
                verification_index.index("Parameterized Box"),
                verification_index.index("TOP Sketch on circular body"),
            )
            self.assertLess(
                verification_index.index("Face anchor follows parent geometry"),
                verification_index.index("Topology-backed corner anchor"),
            )

            verification_case = (
                out / "verification" / "simple-box" / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("Forge code", verification_case)
            self.assertIn("class SimpleBox", verification_case)
            self.assertIn("Verification", verification_case)
            self.assertIn("1 · Basic geometry", verification_case)
            self.assertNotIn(">fundamentals<", verification_case)
            self.assertNotIn(">Qualification<", verification_case)
            for implementation in (
                "pythonscad",
                "pybosl2",
                "cadquery",
                "build123d",
            ):
                reference_source = (
                    ROOT
                    / "examples"
                    / "simple-box"
                    / implementation
                    / "model.py"
                ).read_text(encoding="utf-8")
                self.assertIn(
                    html.escape(
                        reference_source.strip().splitlines()[0],
                        quote=True,
                    ),
                    verification_case,
                )
            self.assertIn(
                "Stable result evidence is not available",
                verification_case,
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
