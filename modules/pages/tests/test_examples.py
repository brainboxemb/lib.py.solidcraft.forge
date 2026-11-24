from pathlib import Path
import json
import tempfile
import unittest
from cad_library_pages.examples import prepare_examples


class ExamplePagesTests(unittest.TestCase):
    def test_public_example_has_evidence_and_fixture_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item, purpose in (("box", "[example, verification]"), ("fixture", "verification")):
                owner = root / "examples" / item
                owner.mkdir(parents=True)
                (owner / "model.yml").write_text(f"title: {item}\npurpose: {purpose}\n")
                (owner / "ci.yml").write_text(f"id: {item}\n")
            evidence = root / "build" / "examples" / "box"
            (evidence / "verification").mkdir(parents=True)
            (evidence / "result.json").write_text(json.dumps({"id":"box","status":"pass","builder":"cadquery","verification_status":"pass"}))
            (evidence / "source.json").write_text(json.dumps({"source_sha":"test-sha"}))
            (evidence / "model.stl").write_text("mesh")
            (evidence / "verification/verification.json").write_text("{}")
            site = root / "site"
            prepare_examples(root, site, root/"build")
            page = site / "content/examples/box/index.md"
            self.assertIn("test-sha", page.read_text())
            self.assertTrue((site/"static/examples/box/model.stl").is_file())
            self.assertFalse((site/"content/examples/fixture").exists())
