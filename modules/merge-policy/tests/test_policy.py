import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cad_model_merge_policy.__main__ import (
    dispatch_workflow,
    merge_required,
    pull_request_files,
    require_conflicted_permanent_pr,
    require_green_ci,
    require_main_governance_paths,
    run_resolved,
)
from cad_model_merge_policy.policy import (
    MergePolicyError,
    is_main_governance,
    is_permanent_merge,
    merge_method,
)


def workflow_run(
    run_id,
    status,
    conclusion,
    created_at,
    *prs,
    path=".github/workflows/ci.yml",
):
    return {
        "id": run_id,
        "event": "pull_request",
        "path": path,
        "status": status,
        "conclusion": conclusion,
        "created_at": created_at,
        "pull_requests": [{"number": number} for number in prs],
    }


class MergePolicyTests(unittest.TestCase):
    def test_open_pull_request_requires_merge(self):
        self.assertTrue(merge_required({"state": "open", "merged": False}))

    def test_already_merged_pull_request_is_idempotent_noop(self):
        self.assertFalse(
            merge_required(
                {
                    "state": "closed",
                    "merged": True,
                    "merge_commit_sha": "abc123",
                }
            )
        )

    def test_closed_unmerged_pull_request_is_rejected(self):
        with self.assertRaisesRegex(MergePolicyError, "closed without merge"):
            merge_required({"state": "closed", "merged": False})

    def test_feature_to_dev_is_squash(self):
        self.assertEqual(merge_method(head="issue/10-change", base="dev"), "squash")

    def test_experimental_routes(self):
        self.assertEqual(merge_method(head="feature/73-work", base="exp"), "squash")
        self.assertEqual(merge_method(head="dev", base="exp"), "merge")
        self.assertEqual(merge_method(head="exp", base="dev"), "merge")
        for head, base in (("exp", "main"), ("main", "exp"), ("release/v1", "exp"), ("release/v1", "dev")):
            with self.subTest(head=head, base=base), self.assertRaises(MergePolicyError):
                merge_method(head=head, base=base)

    def test_governance_docs_to_main_is_squash(self):
        self.assertTrue(
            is_main_governance(head="docs/123-plan", base="main")
        )
        self.assertEqual(
            merge_method(head="docs/123-plan", base="main"),
            "squash",
        )
        self.assertFalse(
            is_main_governance(head="docs/123-plan", base="dev")
        )

    @patch("cad_model_merge_policy.__main__.api")
    def test_main_governance_paths_are_allowlisted(self, api):
        api.return_value = [
            {"filename": "AGENTS.md"},
            {"filename": "docs/plan.md"},
            {"filename": "docs/handoff.md"},
        ]
        require_main_governance_paths("owner/repo", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_main_governance_rejects_non_governance_path(self, api):
        api.return_value = [
            {"filename": "docs/plan.md"},
            {"filename": "cadlib/src/package.py"},
        ]
        with self.assertRaisesRegex(MergePolicyError, "forbidden"):
            require_main_governance_paths("owner/repo", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_pull_request_files_paginates_before_validation(self, api):
        api.side_effect = [
            [{"filename": "docs/plan.md"} for _ in range(100)],
            [{"filename": "README.md"}],
        ]
        self.assertEqual(
            len(pull_request_files("owner/repo", 25, "token")),
            101,
        )
        self.assertEqual(api.call_count, 2)
        with patch(
            "cad_model_merge_policy.__main__.pull_request_files",
            return_value=("docs/plan.md", "README.md"),
        ):
            with self.assertRaisesRegex(MergePolicyError, "README.md"):
                require_main_governance_paths("owner/repo", 25, "token")

    def test_release_to_main_is_squash(self):
        self.assertEqual(
            merge_method(head="release/v1.2.3", base="main"),
            "squash",
        )

    def test_dev_to_main_is_merge_commit(self):
        self.assertEqual(merge_method(head="dev", base="main"), "merge")

    def test_main_to_dev_is_merge_commit(self):
        self.assertEqual(merge_method(head="main", base="dev"), "merge")

    def test_feature_to_main_is_rejected(self):
        with self.assertRaises(MergePolicyError):
            merge_method(head="issue/10-change", base="main")

    def test_reviewed_recovery_is_only_for_direct_permanent_merges(self):
        for head, base in (
            ("dev", "main"),
            ("main", "dev"),
            ("dev", "exp"),
            ("exp", "dev"),
        ):
            with self.subTest(head=head, base=base):
                self.assertTrue(is_permanent_merge(head=head, base=base))
        for head, base in (
            ("sync/90-resolution", "exp"),
            ("release/v1.2.3", "main"),
            ("docs/90-plan", "main"),
            ("feature/90-work", "dev"),
        ):
            with self.subTest(head=head, base=base):
                self.assertFalse(is_permanent_merge(head=head, base=base))

    @patch("cad_model_merge_policy.__main__.api")
    def test_resolved_recovery_rejects_temporary_original_pr(self, api):
        api.return_value = {
            "state": "open",
            "merged": False,
            "draft": False,
            "mergeable": False,
            "base": {"ref": "exp", "sha": "a" * 40},
            "head": {
                "ref": "sync/90-resolution",
                "sha": "b" * 40,
                "repo": {"full_name": "owner/repo"},
            },
        }
        with self.assertRaisesRegex(MergePolicyError, "direct permanent merge"):
            require_conflicted_permanent_pr(
                "owner/repo",
                25,
                "a" * 40,
                "b" * 40,
                "token",
            )

    def test_resolved_recovery_creates_exact_two_parent_commit(self):
        command = "\n".join(
            [
                "/merge-resolved",
                "base " + "a" * 40,
                "head " + "b" * 40,
                "resolution-pr 26",
                "resolution resolve/25-dev-exp " + "c" * 40 + " " + "d" * 40,
            ]
        )
        args = SimpleNamespace(
            command=command,
            repository="owner/repo",
            pull_request_number=25,
            resolution_prefix="resolve/",
        )
        pr = {
            "base": {"ref": "exp", "sha": "a" * 40},
            "head": {"ref": "dev", "sha": "b" * 40},
        }
        review = {"number": 26}
        created = {
            "sha": "e" * 40,
            "tree": {"sha": "d" * 40},
            "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
        }

        with patch(
            "cad_model_merge_policy.__main__.require_conflicted_permanent_pr",
            side_effect=[pr, pr],
        ), patch(
            "cad_model_merge_policy.__main__.require_green_ci"
        ), patch(
            "cad_model_merge_policy.__main__.require_resolution_review",
            side_effect=[review, review],
        ), patch(
            "cad_model_merge_policy.__main__.require_branch_sha"
        ) as require_ref, patch(
            "cad_model_merge_policy.__main__.resolution_commit_tree"
        ) as require_tree, patch(
            "cad_model_merge_policy.__main__.api",
            side_effect=[created, {}],
        ) as api, patch(
            "cad_model_merge_policy.__main__.dispatch_workflow"
        ) as dispatch, patch(
            "cad_model_merge_policy.__main__.close_pr_if_open"
        ) as close_pr, patch(
            "cad_model_merge_policy.__main__.delete_resolution_ref"
        ) as delete_ref:
            self.assertEqual(run_resolved(args, "token"), "e" * 40)

        create = api.call_args_list[0]
        self.assertEqual(create.args[:2], ("owner/repo", "git/commits"))
        self.assertEqual(create.kwargs["method"], "POST")
        self.assertEqual(
            create.kwargs["body"]["parents"],
            ["a" * 40, "b" * 40],
        )
        self.assertEqual(create.kwargs["body"]["tree"], "d" * 40)

        advance = api.call_args_list[1]
        self.assertEqual(
            advance.args[:2],
            ("owner/repo", "git/refs/heads/exp"),
        )
        self.assertEqual(advance.kwargs["method"], "PATCH")
        self.assertEqual(
            advance.kwargs["body"],
            {"sha": "e" * 40, "force": False},
        )
        self.assertEqual(require_ref.call_count, 6)
        self.assertEqual(require_tree.call_count, 2)
        dispatch.assert_any_call("owner/repo", "ci.yml", "exp", "token")
        dispatch.assert_any_call(
            "owner/repo", "branch-cleanup.yml", "exp", "token"
        )
        self.assertEqual(close_pr.call_count, 2)
        delete_ref.assert_called_once_with(
            "owner/repo",
            "resolve/25-dev-exp",
            "c" * 40,
            "token",
        )

    def test_workflow_forwards_full_owner_command(self):
        root = Path(__file__).resolve().parents[3]
        workflow = (root / ".github/workflows/merge-policy.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("MERGE_COMMAND: ${{ github.event.comment.body }}", workflow)
        self.assertIn('--command "$MERGE_COMMAND"', workflow)
        self.assertIn('--resolution-prefix "resolve/"', workflow)

    @patch("cad_model_merge_policy.__main__.api")
    def test_green_ci_ignores_unrelated_workflow_runs(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    30,
                    "in_progress",
                    None,
                    "2026-01-03T00:00:00Z",
                    25,
                    path=".github/workflows/merge-policy.yml",
                ),
                workflow_run(
                    20,
                    "completed",
                    "success",
                    "2026-01-02T00:00:00Z",
                    25,
                ),
            ]
        }
        require_green_ci("owner/repo", "sha", 25, "token")
        self.assertIn(
            "event=pull_request",
            api.call_args.args[1],
        )
        self.assertIn("head_sha=sha", api.call_args.args[1])

    @patch("cad_model_merge_policy.__main__.api")
    def test_newer_green_ci_supersedes_historical_failure(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    101,
                    "completed",
                    "failure",
                    "2026-01-01T00:00:00Z",
                    25,
                ),
                workflow_run(
                    103,
                    "completed",
                    "success",
                    "2026-01-03T00:00:00Z",
                    25,
                ),
                workflow_run(
                    102,
                    "completed",
                    "failure",
                    "2026-01-02T00:00:00Z",
                    25,
                ),
            ]
        }
        require_green_ci("owner/repo", "sha", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_latest_pending_ci_blocks_merge_even_after_older_green(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    20,
                    "completed",
                    "success",
                    "2026-01-01T00:00:00Z",
                    25,
                ),
                workflow_run(
                    21,
                    "in_progress",
                    None,
                    "2026-01-02T00:00:00Z",
                    25,
                ),
            ]
        }
        with self.assertRaisesRegex(MergePolicyError, "still running"):
            require_green_ci("owner/repo", "sha", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_latest_failed_ci_blocks_merge_even_after_older_green(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    20,
                    "completed",
                    "success",
                    "2026-01-01T00:00:00Z",
                    25,
                ),
                workflow_run(
                    21,
                    "completed",
                    "failure",
                    "2026-01-02T00:00:00Z",
                    25,
                ),
            ]
        }
        with self.assertRaisesRegex(MergePolicyError, "not green"):
            require_green_ci("owner/repo", "sha", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_same_timestamp_uses_higher_run_id_as_latest(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    20,
                    "completed",
                    "failure",
                    "2026-01-01T00:00:00Z",
                    25,
                ),
                workflow_run(
                    21,
                    "completed",
                    "success",
                    "2026-01-01T00:00:00Z",
                    25,
                ),
            ]
        }
        require_green_ci("owner/repo", "sha", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_missing_pr_specific_ci_blocks_merge(self, api):
        api.return_value = {
            "workflow_runs": [
                workflow_run(
                    20,
                    "completed",
                    "success",
                    "2026-01-01T00:00:00Z",
                    99,
                ),
                workflow_run(
                    21,
                    "completed",
                    "success",
                    "2026-01-02T00:00:00Z",
                    25,
                    path=".github/workflows/merge-policy.yml",
                ),
            ]
        }
        with self.assertRaisesRegex(MergePolicyError, "no central ci"):
            require_green_ci("owner/repo", "sha", 25, "token")

    @patch("cad_model_merge_policy.__main__.api")
    def test_dispatch_workflow_targets_local_workflow_and_base_ref(self, api):
        dispatch_workflow("owner/repo", "ci.yml", "dev", "token")
        api.assert_called_once_with(
            "owner/repo",
            "actions/workflows/ci.yml/dispatches",
            "token",
            method="POST",
            body={"ref": "dev"},
        )

    @patch("cad_model_merge_policy.__main__.api")
    def test_cleanup_workflow_uses_same_target_ref(self, api):
        dispatch_workflow("owner/repo", "branch-cleanup.yml", "dev", "token")
        api.assert_called_once_with(
            "owner/repo",
            "actions/workflows/branch-cleanup.yml/dispatches",
            "token",
            method="POST",
            body={"ref": "dev"},
        )


if __name__ == "__main__":
    unittest.main()
