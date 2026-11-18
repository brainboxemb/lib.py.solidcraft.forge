"""Tests for generated build and Pages branch layout."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts" / "generated_output.py"
    spec = importlib.util.spec_from_file_location("generated_output", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeneratedOutputTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_build_layout_follows_example_and_implementation(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            output = root / "output"
            target = root / "build"

            (repo / "examples" / "simple-box" / "scpf").mkdir(parents=True)
            (repo / "examples" / "simple-box" / "cadquery").mkdir(parents=True)
            (output / "native" / "simple-box").mkdir(parents=True)
            (output / "references" / "simple-box" / "cadquery").mkdir(
                parents=True
            )
            (output / "qualification").mkdir(parents=True)
            (output / "diagrams").mkdir(parents=True)

            (output / "simple-box.json").write_text(
                '{"commands": []}\n',
                encoding="utf-8",
            )
            (output / "native" / "simple-box" / "model.step").write_bytes(
                b"step"
            )
            (
                output
                / "references"
                / "simple-box"
                / "cadquery"
                / "model.stl"
            ).write_bytes(b"stl")
            (output / "references" / "summary.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (output / "qualification" / "results.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (output / "diagrams" / "flow.svg").write_text(
                "<svg/>\n",
                encoding="utf-8",
            )

            metadata = {
                "scope": "pr",
                "source_ref": "feature/test",
                "source_commit": "abc123",
                "pull_request": 42,
                "forge_version": "0.1.1",
                "solidcraft_version": None,
                "workflow_run_id": "99",
                "qualification": {
                    "level": "q1-q2-fast",
                    "status": "pass",
                },
            }
            self.module.assemble_build(
                output,
                target,
                metadata,
                repo_root=repo,
            )

            self.assertTrue(
                (
                    target
                    / "examples"
                    / "simple-box"
                    / "scpf"
                    / "solidcraft.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    target
                    / "examples"
                    / "simple-box"
                    / "scpf"
                    / "model.step"
                ).is_file()
            )
            self.assertTrue(
                (
                    target
                    / "examples"
                    / "simple-box"
                    / "cadquery"
                    / "model.stl"
                ).is_file()
            )
            self.assertTrue(
                (target / "qualification" / "results.json").is_file()
            )
            self.assertTrue(
                (
                    target
                    / "qualification"
                    / "references-summary.json"
                ).is_file()
            )
            self.assertTrue(
                (target / "qualification" / "diagrams" / "flow.svg").is_file()
            )
            self.assertFalse((target / "native").exists())
            self.assertFalse((target / "references").exists())

            build = json.loads(
                (target / "build.json").read_text(encoding="utf-8")
            )
            self.assertEqual(build["scope"], "pr")
            self.assertEqual(build["pull_request"], 42)
            self.assertEqual(build["source_commit"], "abc123")
            self.module.verify_build(target, "abc123")

    def test_verify_rejects_producer_oriented_top_level_output(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "native").mkdir()
            (root / "build.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "scope": "main",
                        "source_commit": "abc",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "unexpected top-level build output",
            ):
                self.module.verify_build(root, "abc")

    def test_stable_pages_replaces_root_and_preserves_previews(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = root / "site"
            current = root / "current"
            destination = root / "destination"

            site.mkdir()
            (site / "index.html").write_text("new", encoding="utf-8")
            (site / "provenance.json").write_text("{}\n", encoding="utf-8")

            (current / "previews" / "pr-7").mkdir(parents=True)
            (current / "previews" / "pr-7" / "index.html").write_text(
                "preview",
                encoding="utf-8",
            )
            destination.mkdir()
            (destination / "old.html").write_text("old", encoding="utf-8")

            self.module.prepare_stable_pages(site, current, destination)

            self.assertEqual(
                (destination / "index.html").read_text(encoding="utf-8"),
                "new",
            )
            self.assertFalse((destination / "old.html").exists())
            self.assertEqual(
                (
                    destination
                    / "previews"
                    / "pr-7"
                    / "index.html"
                ).read_text(encoding="utf-8"),
                "preview",
            )

    def test_remove_pr_is_scoped_to_requested_output(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pr" / "7").mkdir(parents=True)
            (root / "pr" / "8").mkdir(parents=True)

            changed = self.module.remove_pr(root, "build", 7)

            self.assertTrue(changed)
            self.assertFalse((root / "pr" / "7").exists())
            self.assertTrue((root / "pr" / "8").is_dir())


if __name__ == "__main__":
    unittest.main()
