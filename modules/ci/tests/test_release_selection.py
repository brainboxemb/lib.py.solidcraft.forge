import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cad_library_ci.__main__ import selection
from cad_library_ci.config import ConfigError


PROJECT = SimpleNamespace(
    stable_branch="main",
    development_branch="dev",
)


class ReleaseSelectionTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_base")
    def test_release_pr_selects_library_and_release_only(self, changed):
        changed.return_value = (
            "CHANGELOG.md",
            "cadlib/pyproject.toml",
        )
        plan, paths, full, release_only = selection(
            Path("."),
            PROJECT,
            "release/v1.2.3",
            (),
        )
        self.assertEqual(plan.modules, ("release",))
        self.assertEqual(plan.models, ())
        self.assertTrue(plan.library)
        self.assertIsNone(paths)
        self.assertFalse(full)
        self.assertTrue(release_only)

    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_base")
    def test_release_pr_rejects_non_release_paths(self, changed):
        changed.return_value = (
            "CHANGELOG.md",
            "cadlib/src/demo.py",
        )
        with self.assertRaisesRegex(ConfigError, "non-release"):
            selection(Path("."), PROJECT, "release/v1.2.3", ())

    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_SHA": "a" * 40,
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_release_metadata_push_is_lightweight(self, changed):
        changed.return_value = ("CHANGELOG.md",)
        plan, paths, full, release_only = selection(
            Path("."),
            PROJECT,
            "main",
            (),
        )
        self.assertEqual(plan.modules, ("release",))
        self.assertEqual(plan.models, ())
        self.assertTrue(plan.library)
        self.assertIsNone(paths)
        self.assertFalse(full)
        self.assertTrue(release_only)

    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_SHA": "b" * 40,
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_product_push_remains_full(self, changed):
        changed.return_value = ("cadlib/src/demo.py",)
        plan, paths, full, release_only = selection(
            Path("."),
            PROJECT,
            "main",
            (),
        )
        self.assertIsNone(plan.modules)
        self.assertIsNone(plan.models)
        self.assertTrue(plan.library)
        self.assertIsNone(paths)
        self.assertTrue(full)
        self.assertFalse(release_only)


if __name__ == "__main__":
    unittest.main()
