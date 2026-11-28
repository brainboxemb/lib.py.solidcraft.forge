import unittest
from unittest.mock import patch

from cad_library_ci.history import (
    changed_paths,
    changed_paths_from_base,
    changed_paths_from_parent,
    discover_reusable_pr_qualification,
    last_successful_dev_sha,
    reusable_pr_qualification,
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

    @patch("cad_library_ci.history._json")
    def test_reusable_pr_qualification_accepts_merge_policy_binding(self, get):
        source = "a" * 40
        head = "b" * 40
        base = "c" * 40
        get.side_effect = [
            {
                "number": 12,
                "state": "closed",
                "merged_at": "2026-01-01T00:00:00Z",
                "merge_commit_sha": source,
                "base": {"ref": "exp", "sha": base},
                "head": {
                    "ref": "issue/12-change",
                    "sha": head,
                    "repo": {"full_name": "owner/repo"},
                },
            },
            {
                "id": 31,
                "event": "pull_request",
                "path": ".github/workflows/ci.yml",
                "head_sha": head,
                "head_branch": "issue/12-change",
                "status": "completed",
                "conclusion": "success",
            },
            {
                "artifacts": [
                    {
                        "id": 99,
                        "name": "cad-qualification",
                        "expired": False,
                    }
                ]
            },
        ]

        evidence = reusable_pr_qualification(
            repository="owner/repo",
            branch="exp",
            token="token",
            source_sha=source,
            pr_number=12,
            head_sha=head,
            run_id=31,
        )
        self.assertEqual(evidence.pr_number, 12)
        self.assertEqual(evidence.head_sha, head)
        self.assertEqual(evidence.base_sha, base)
        self.assertEqual(evidence.run_id, 31)
        self.assertEqual(evidence.artifact_id, 99)

    @patch("cad_library_ci.history._json")
    def test_reusable_pr_qualification_rejects_failed_bound_run(self, get):
        source = "d" * 40
        head = "e" * 40
        get.side_effect = [
            {
                "number": 13,
                "state": "closed",
                "merged_at": "2026-01-01T00:00:00Z",
                "merge_commit_sha": source,
                "base": {"ref": "exp", "sha": "f" * 40},
                "head": {
                    "ref": "issue/13-change",
                    "sha": head,
                    "repo": {"full_name": "owner/repo"},
                },
            },
            {
                "id": 42,
                "event": "pull_request",
                "path": ".github/workflows/ci.yml",
                "head_sha": head,
                "head_branch": "issue/13-change",
                "status": "completed",
                "conclusion": "failure",
            },
        ]
        self.assertIsNone(
            reusable_pr_qualification(
                repository="owner/repo",
                branch="exp",
                token="token",
                source_sha=source,
                pr_number=13,
                head_sha=head,
                run_id=42,
            )
        )

    @patch("cad_library_ci.history._json")
    def test_reusable_pr_qualification_rejects_wrong_binding(self, get):
        source = "1" * 40
        head = "2" * 40
        get.return_value = {
            "number": 14,
            "state": "closed",
            "merged_at": "2026-01-01T00:00:00Z",
            "merge_commit_sha": source,
            "base": {"ref": "dev", "sha": "3" * 40},
            "head": {
                "ref": "issue/14-change",
                "sha": head,
                "repo": {"full_name": "owner/repo"},
            },
        }
        self.assertIsNone(
            reusable_pr_qualification(
                repository="owner/repo",
                branch="exp",
                token="token",
                source_sha=source,
                pr_number=14,
                head_sha=head,
                run_id=43,
            )
        )

    @patch("cad_library_ci.history._json")
    def test_discovery_uses_newest_green_run_for_associated_merged_pr(self, get):
        source = "4" * 40
        head = "5" * 40
        base = "6" * 40
        get.side_effect = [
            [
                {
                    "number": 15,
                    "state": "closed",
                    "merged_at": "2026-01-01T00:00:00Z",
                    "merge_commit_sha": source,
                    "base": {"ref": "exp", "sha": base},
                    "head": {
                        "ref": "issue/15-change",
                        "sha": head,
                        "repo": {"full_name": "owner/repo"},
                    },
                }
            ],
            {
                "workflow_runs": [
                    {
                        "id": 50,
                        "event": "pull_request",
                        "path": ".github/workflows/ci.yml",
                        "head_sha": head,
                        "head_branch": "issue/15-change",
                        "created_at": "2026-01-01T00:00:00Z",
                        "status": "completed",
                        "conclusion": "success",
                    },
                    {
                        "id": 51,
                        "event": "pull_request",
                        "path": ".github/workflows/ci.yml",
                        "head_sha": head,
                        "head_branch": "issue/15-change",
                        "created_at": "2026-01-02T00:00:00Z",
                        "status": "completed",
                        "conclusion": "success",
                    },
                ]
            },
            {
                "artifacts": [
                    {
                        "id": 101,
                        "name": "cad-qualification",
                        "expired": False,
                    }
                ]
            },
        ]
        evidence = discover_reusable_pr_qualification(
            repository="owner/repo",
            branch="exp",
            token="token",
            source_sha=source,
        )
        self.assertEqual(evidence.pr_number, 15)
        self.assertEqual(evidence.head_sha, head)
        self.assertEqual(evidence.base_sha, base)
        self.assertEqual(evidence.run_id, 51)
        self.assertEqual(evidence.artifact_id, 101)

    @patch("cad_library_ci.history._json")
    def test_discovery_falls_back_when_newest_candidate_run_failed(self, get):
        source = "7" * 40
        head = "8" * 40
        get.side_effect = [
            [
                {
                    "number": 16,
                    "state": "closed",
                    "merged_at": "2026-01-01T00:00:00Z",
                    "merge_commit_sha": source,
                    "base": {"ref": "exp", "sha": "9" * 40},
                    "head": {
                        "ref": "issue/16-change",
                        "sha": head,
                        "repo": {"full_name": "owner/repo"},
                    },
                }
            ],
            {
                "workflow_runs": [
                    {
                        "id": 61,
                        "event": "pull_request",
                        "path": ".github/workflows/ci.yml",
                        "head_sha": head,
                        "head_branch": "issue/16-change",
                        "created_at": "2026-01-02T00:00:00Z",
                        "status": "completed",
                        "conclusion": "failure",
                    },
                    {
                        "id": 60,
                        "event": "pull_request",
                        "path": ".github/workflows/ci.yml",
                        "head_sha": head,
                        "head_branch": "issue/16-change",
                        "created_at": "2026-01-01T00:00:00Z",
                        "status": "completed",
                        "conclusion": "success",
                    },
                ]
            },
        ]
        self.assertIsNone(
            discover_reusable_pr_qualification(
                repository="owner/repo",
                branch="exp",
                token="token",
                source_sha=source,
            )
        )

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
