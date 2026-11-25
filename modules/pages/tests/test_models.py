from pathlib import Path
import json
import tempfile
import unittest

from cad_library_pages.models import prepare_models


class ModelPagesTests(unittest.TestCase):
    def test_multiple_purposes_and_named_stages_are_projected_without_copying(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "site/config/_default"
            config.mkdir(parents=True)
            (config / "hugo.toml").write_text(
                '[params]\ncadSourceRepository = "owner/repo"\n'
            )
            sections = root / "docs/verification"
            sections.mkdir(parents=True)
            (sections / "sections.yml").write_text(
                "schema: 1\n"
                "sections:\n"
                "  later:\n"
                "    priority: 20\n"
                "    label: 2 · Later\n"
                "    description: Later cases.\n"
                "  fundamentals:\n"
                "    priority: 10\n"
                "    label: 1 · Basic geometry\n"
                "    description: Primitive geometry.\n"
            )
            for item, purpose in (
                ("box", "[example, verification]"),
                ("fixture", "[verification]"),
            ):
                owner = root / "models" / item
                owner.mkdir(parents=True)
                (owner / "model.yml").write_text(
                    f"title: {item}\npurpose: {purpose}\n"
                    "section: fundamentals\npriority: 20\n"
                )
                (owner / "ci.yml").write_text(
                    f"id: {item}\nprimary: cadquery\nimplementations:\n  - id: cadquery\n    source: model.py\n"
                )

                (owner / "model.py").write_text("value = 42\n")

            build_scope = root / "build" / "dev"
            evidence = build_scope / "models" / "box"
            (evidence / "cadquery/verification/geometry").mkdir(parents=True)
            (evidence / "legacy/verification").mkdir(parents=True)
            (evidence / "result.json").write_text(json.dumps({
                "id": "box",
                "status": "pass",
                "primary": "cadquery",
                "implementations": {
                    "cadquery": {
                        "builder": "builder-cadquery",
                        "build_status": "pass",
                        "verification_status": "pass",
                        "verification_stages": {
                            "geometry": {
                                "status": "pass",
                                "adapter": "mesh-geometry",
                                "runtime": "reference:1",
                            }
                        },
                    },
                    "legacy": {
                        "builder": "builder-legacy",
                        "build_status": "pass",
                        "verification_status": "pass",
                    },
                },
            }))
            (evidence / "source.json").write_text(
                json.dumps({"source_sha": "test-sha"})
            )
            (evidence / "model.png").write_text("owner-level image")
            (evidence / "cadquery/model.png").write_text("implementation image")
            (evidence / "model.stl").write_text("mesh")
            for implementation in ("cadquery", "legacy"):
                (evidence / implementation / "model.stl").write_text("mesh")
                (evidence / implementation / "result.json").write_text("{}")
                (evidence / implementation / "verification/verification.json").write_text("{}")
            (evidence / "cadquery/verification/geometry/verification.json").write_text("{}")

            site = root / "staged-site"
            prepare_models(root, site, build_scope)
            page = site / "content/examples/box/index.md"
            content = page.read_text()
            self.assertIn("test-sha", content)
            self.assertNotIn('"verificationsection"', content)
            self.assertNotIn("build/dev/models/box/model.png", content)
            self.assertIn("value = 42", content)
            self.assertIn("model.py", content)
            self.assertIn(
                "https://github.com/owner/repo/blob/build/dev/models/box/model.stl",
                content,
            )
            self.assertIn(
                "https://raw.githubusercontent.com/owner/repo/build/dev/models/box/cadquery/model.png",
                content,
            )
            self.assertIn(
                "`geometry`: status=pass, adapter=mesh-geometry, runtime=reference:1",
                content,
            )
            self.assertIn(
                "models/box/cadquery/verification/geometry/verification.json",
                content,
            )
            self.assertIn("**legacy** — builder-legacy", content)
            self.assertFalse((site / "static/models/box/model.stl").exists())
            self.assertFalse((site / "content/examples/fixture").exists())
            self.assertTrue((site / "content/verification/fixture/index.md").is_file())
            verification_box = site / "content/verification/box/index.md"
            self.assertTrue(verification_box.is_file())
            self.assertIn('"verificationsection": "fundamentals"', verification_box.read_text())
            catalog = json.loads(
                (site / "assets/cad/verification_sections.json").read_text()
            )
            self.assertEqual(
                catalog["sections"],
                [
                    {
                        "id": "fundamentals",
                        "priority": 10,
                        "label": "1 · Basic geometry",
                        "description": "Primitive geometry.",
                        "models": [
                            {"id": "box", "priority": 20, "title": "box"},
                            {"id": "fixture", "priority": 20, "title": "fixture"},
                        ],
                    },
                    {
                        "id": "later",
                        "priority": 20,
                        "label": "2 · Later",
                        "description": "Later cases.",
                        "models": [],
                    },
                ],
            )
            self.assertIn('"/models/box/"', content)
            self.assertEqual(list(site.rglob("*.stl")), [])

    def test_unknown_verification_section_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "site/config/_default"
            config.mkdir(parents=True)
            (config / "hugo.toml").write_text(
                '[params]\ncadSourceRepository = "owner/repo"\n'
            )
            sections = root / "docs/verification"
            sections.mkdir(parents=True)
            (sections / "sections.yml").write_text(
                "schema: 1\nsections:\n"
                "  fundamentals:\n"
                "    priority: 10\n"
                "    label: Basic\n"
                "    description: Basic cases.\n"
            )
            owner = root / "models/box"
            owner.mkdir(parents=True)
            (owner / "model.yml").write_text(
                "title: box\npurpose: verification\nsection: missing\n"
            )
            (owner / "ci.yml").write_text(
                "id: box\nprimary: cadquery\nimplementations:\n"
                "  - id: cadquery\n    source: model.py\n"
            )
            (owner / "model.py").write_text("value = 42\n")

            with self.assertRaisesRegex(ValueError, "unknown verification section"):
                prepare_models(root, root / "staged-site", None)


if __name__ == "__main__":
    unittest.main()
