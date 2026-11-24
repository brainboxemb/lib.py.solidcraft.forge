from pathlib import Path
import json
import tempfile
import unittest

from cad_library_pages.models import prepare_models


class ModelPagesTests(unittest.TestCase):
    def test_multiple_purposes_are_public_without_copying_build_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "site/config/_default"
            config.mkdir(parents=True)
            (config / "hugo.toml").write_text(
                '[params]\ncadSourceRepository = "owner/repo"\n'
            )
            for item, purpose in (
                ("box", "[example, verification]"),
                ("fixture", "[verification]"),
            ):
                owner = root / "models" / item
                owner.mkdir(parents=True)
                (owner / "model.yml").write_text(
                    f"title: {item}\npurpose: {purpose}\n"
                )
                (owner / "ci.yml").write_text(
                    f"id: {item}\nprimary: cadquery\n"
                )

            build_scope = root / "build" / "dev"
            evidence = build_scope / "models" / "box"
            (evidence / "cadquery/verification").mkdir(parents=True)
            (evidence / "result.json").write_text(json.dumps({
                "id": "box",
                "status": "pass",
                "primary": "cadquery",
                "implementations": {
                    "cadquery": {
                        "builder": "builder-cadquery",
                        "build_status": "pass",
                        "verification_status": "pass",
                    }
                },
            }))
            (evidence / "source.json").write_text(
                json.dumps({"source_sha": "test-sha"})
            )
            (evidence / "model.png").write_text("png")
            (evidence / "model.stl").write_text("mesh")
            (evidence / "cadquery/model.stl").write_text("mesh")
            (evidence / "cadquery/result.json").write_text("{}")
            (evidence / "cadquery/verification/verification.json").write_text("{}")

            site = root / "staged-site"
            prepare_models(root, site, build_scope)
            page = site / "content/models/box/index.md"
            content = page.read_text()
            self.assertIn("test-sha", content)
            self.assertIn(
                "https://github.com/owner/repo/blob/build/dev/models/box/model.stl",
                content,
            )
            self.assertIn(
                "https://raw.githubusercontent.com/owner/repo/build/dev/models/box/model.png",
                content,
            )
            self.assertFalse((site / "static/models/box/model.stl").exists())
            self.assertFalse((site / "content/models/fixture").exists())


if __name__ == "__main__":
    unittest.main()
