"""Tests for hosted PR preview cleanup."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_preview_cleanup_module():
    path = ROOT / "site" / "preview_cleanup.py"
    spec = importlib.util.spec_from_file_location("preview_cleanup", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PreviewCleanupTests(unittest.TestCase):
    def test_preview_path_is_one_directory_per_pr(self):
        cleanup = load_preview_cleanup_module()
        root = Path("/tmp/pages")
        self.assertEqual(
            cleanup.preview_path(root, 123),
            root / "previews" / "pr-123",
        )

    def test_remove_preview_removes_only_requested_pr(self):
        cleanup = load_preview_cleanup_module()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            stable = root / "index.html"
            first = root / "previews" / "pr-123"
            second = root / "previews" / "pr-456"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            stable.write_text("stable", encoding="utf-8")
            (first / "index.html").write_text("first", encoding="utf-8")
            (second / "index.html").write_text("second", encoding="utf-8")

            self.assertTrue(cleanup.remove_preview(root, 123))

            self.assertFalse(first.exists())
            self.assertTrue(second.is_dir())
            self.assertEqual(stable.read_text(encoding="utf-8"), "stable")

    def test_remove_preview_is_noop_when_pr_has_no_preview(self):
        cleanup = load_preview_cleanup_module()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "previews").mkdir()

            self.assertFalse(cleanup.remove_preview(root, 999))

    def test_pull_request_number_must_be_positive(self):
        cleanup = load_preview_cleanup_module()
        with self.assertRaises(ValueError):
            cleanup.preview_path(Path("/tmp/pages"), 0)


if __name__ == "__main__":
    unittest.main()
