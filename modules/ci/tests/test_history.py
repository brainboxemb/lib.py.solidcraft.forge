import unittest
from unittest.mock import patch

from cad_library_ci.history import (
    changed_paths,
    changed_paths_from_base,
    changed_paths_from_parent,
    last_successful_dev_sha,
)


class HistoryTests(unittest.TestCase):
    @patch("cad_library_ci.history._json")
    def test_last_successful_dev_excludes_pull_request_and_current_target(self, get):
        get.return_value = {
            "workflow_runs": [
                {
                    "id": 20,
                    "event": "pull_request",
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": "pr",
                },
                {
                    "id": 19,
                    "event": "push",
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": "target",
                },
                {
                    "id": 18,
                    "event": "push",
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": "baseline",
                },
            ]
        }
        self.assertEqual(
            last_successful_dev_sha(
                repository="owner/repo",
                branch="dev",
                token="token",
                current_run_id=21,
                target_sha="target",
            ),
            "baseline",
        )

    @patch("cad_library_ci.history._json")
    def test_experimental_history_requests_only_exp(self, get):
        get.return_value = {"workflow_runs": []}
        self.assertIsNone(last_successful_dev_sha(repository="owner/repo", branch="exp", token="token", current_run_id=1, target_sha="new"))
        self.assertIn("branch=exp&", get.call_args.args[0])

    @patch("cad_library_ci.history.subprocess.run")
    def test_non_ancestor_baseline_forces_full_fallback(self, run):
        run.return_value.returncode = 1
        self.assertIsNone(changed_paths(".", "old", "new"))

    @patch("cad_library_ci.history.subprocess.run")
    def test_changed_paths_uses_exact_baseline_and_target(self, run):
        ancestor = type("Result", (), {"returncode": 0})()
        diff = type("Result", (), {"stdout": "modules/build/ci.yml\nmodels/box/model.yml\n"})()
        run.side_effect = [ancestor, diff]
        self.assertEqual(
            changed_paths(".", "aaa", "bbb"),
            ("modules/build/ci.yml", "models/box/model.yml"),
        )
        self.assertEqual(
            run.call_args_list[1].args[0],
            ["git", "-C", ".", "diff", "--name-only", "aaa", "bbb", "--"],
        )


    @patch("cad_library_ci.history.changed_paths")
    @patch("cad_library_ci.history.subprocess.run")
    def test_single_parent_delta_uses_parent_as_baseline(self, run, changed):
        run.return_value.stdout = "target parent\n"
        changed.return_value = ("CHANGELOG.md",)
        self.assertEqual(
            changed_paths_from_parent(".", "target"),
            ("CHANGELOG.md",),
        )
        changed.assert_called_once_with(".", "parent", "target")

    @patch("cad_library_ci.history.subprocess.run")
    def test_merge_commit_is_not_release_only_parent_delta(self, run):
        run.return_value.stdout = "target parent1 parent2\n"
        self.assertIsNone(changed_paths_from_parent(".", "target"))

    @patch("cad_library_ci.history.changed_paths")
    @patch("cad_library_ci.history.subprocess.run")
    def test_pr_delta_uses_remote_base_merge_base(self, run, changed):
        run.return_value.returncode = 0
        run.return_value.stdout = "base-sha\n"
        changed.return_value = ("cadlib/pyproject.toml",)
        self.assertEqual(
            changed_paths_from_base(".", "main", "HEAD"),
            ("cadlib/pyproject.toml",),
        )
        changed.assert_called_once_with(".", "base-sha", "HEAD")

if __name__ == "__main__":
    unittest.main()
