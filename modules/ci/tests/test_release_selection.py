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
    docs_only_prefixes=(),
    docs_only_modules=(),
)

DOC_PROJECT = SimpleNamespace(
    stable_branch="main",
    development_branch="dev",
    docs_only_prefixes=("docs/",),
    docs_only_modules=("ci",),
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
    def test_docs_only_pr_uses_lightweight_configured_selection(self, changed):
        changed.return_value = ("docs/plan.md", "docs/manual.md")
        plan, paths, full, release_only = selection(
            Path("."),
            DOC_PROJECT,
            "docs/465-plan",
            (),
        )
        self.assertEqual(plan.modules, ("ci",))
        self.assertEqual(plan.models, ())
        self.assertFalse(plan.library)
        self.assertEqual(paths, changed.return_value)
        self.assertFalse(full)
        self.assertFalse(release_only)

    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.load_build", return_value=None)
    @patch("cad_library_ci.__main__.changed_paths_from_base")
    def test_mixed_docs_and_source_pr_falls_back_to_normal_selection(
        self,
        changed,
        _load_build,
    ):
        changed.return_value = ("docs/plan.md", "cadlib/src/demo.py")
        plan, paths, full, release_only = selection(
            Path("."),
            DOC_PROJECT,
            "issue/465-mixed",
            (),
        )
        self.assertIsNone(plan.modules)
        self.assertIsNone(plan.models)
        self.assertTrue(plan.library)
        self.assertIsNone(paths)
        self.assertTrue(full)
        self.assertFalse(release_only)

    @patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_SHA": "old-event-sha", "CAD_SOURCE_SHA": "current-checked-out-sha"}, clear=True)
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_dispatch_prefers_checked_out_source_sha(self, changed):
        changed.return_value = ("cadlib/src/demo.py",)
        selection(Path("."), PROJECT, "main", ())
        changed.assert_called_once_with(Path("."), "current-checked-out-sha")

    @patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GH_TOKEN": "token", "GITHUB_REPOSITORY": "owner/repo", "GITHUB_RUN_ID": "42", "GITHUB_SHA": "old-event-sha", "CAD_SOURCE_SHA": "current-checked-out-sha"}, clear=True)
    @patch("cad_library_ci.__main__.changed_paths", return_value=())
    @patch("cad_library_ci.__main__.last_successful_dev_sha", return_value="baseline")
    def test_development_dispatch_prefers_checked_out_source_sha(self, history, changed):
        selection(Path("."), PROJECT, "dev", ())
        self.assertEqual(history.call_args.kwargs["target_sha"], "current-checked-out-sha")
        changed.assert_called_once_with(Path("."), "baseline", "current-checked-out-sha")

    def test_experimental_integration_requires_full_qualification(self):
        for head, base in (("exp", "dev"), ("dev", "exp")):
            with self.subTest(head=head, base=base), patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": base}, clear=True):
                plan, paths, full, release_only = selection(Path("."), PROJECT, head, ())
                self.assertTrue(full)
                self.assertTrue(plan.library)
                self.assertFalse(release_only)

    @patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push", "GH_TOKEN": "token", "GITHUB_REPOSITORY": "owner/repo", "GITHUB_SHA": "new", "GITHUB_RUN_ID": "42"}, clear=True)
    @patch("cad_library_ci.__main__.changed_paths", return_value=())
    @patch("cad_library_ci.__main__.last_successful_dev_sha", return_value="old")
    def test_exp_uses_own_incremental_history(self, history, changed):
        plan, paths, full, release_only = selection(Path("."), PROJECT, "exp", ())
        self.assertEqual(history.call_args.kwargs["branch"], "exp")
        self.assertEqual(plan.branch, "exp")
        self.assertFalse(full)
        self.assertFalse(release_only)

    @patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}, clear=True)
    def test_first_experimental_build_is_full(self):
        plan, paths, full, release_only = selection(Path("."), PROJECT, "exp", ())
        self.assertTrue(full)
        self.assertTrue(plan.library)
        self.assertFalse(release_only)

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
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_SHA": "c" * 40,
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_release_metadata_dispatch_is_lightweight(self, changed):
        changed.return_value = (
            "CHANGELOG.md",
            "cadlib/pyproject.toml",
        )
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
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_SHA": "d" * 40,
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_product_dispatch_remains_full(self, changed):
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

    @patch.dict(
        os.environ,
        {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_SHA": "e" * 40,
        },
        clear=True,
    )
    @patch("cad_library_ci.__main__.changed_paths_from_parent")
    def test_stable_merge_commit_dispatch_falls_back_to_full(self, changed):
        changed.return_value = None
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
