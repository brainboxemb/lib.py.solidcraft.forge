from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "merge-policy.yml"


class MergePolicyWorkflowTests(unittest.TestCase):
    def test_merge_workflow_delegates_policy_and_requires_green_checks(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("issue_comment:", text)
        self.assertIn("github.event.comment.body == '/merge'", text)
        self.assertIn("github.actor == github.repository_owner", text)

        self.assertIn("pull-requests: write", text)
        self.assertIn("issues: write", text)
        self.assertIn("checks: read", text)
        self.assertIn("statuses: read", text)
        self.assertIn("actions: write", text)
        self.assertIn("contents: write", text)

        self.assertIn("scripts/merge_policy.py", text)
        self.assertIn("check-runs?per_page=100", text)
        self.assertNotIn("filter=latest", text)
        self.assertIn("sort_by(.name, (.started_at // \"\"), .id)", text)
        self.assertIn("group_by(.name)", text)
        self.assertIn("map(last)", text)
        self.assertIn('STATUS_COUNT="$(jq', text)
        self.assertIn('merge_method="$METHOD"', text)
        self.assertIn('sha="$HEAD_SHA"', text)

        self.assertIn("DIRECT_PROMOTION", text)
        self.assertIn("CLEANUP_HEAD", text)
        self.assertIn("INTEGRATE_BASE", text)
        self.assertIn("git/refs/heads/$HEAD_REF", text)
        self.assertIn("temporary head deleted", text)
        self.assertIn("long-lived lane recreated at merge commit", text)
        self.assertIn("actions/workflows/scpf.yml/dispatches", text)
        self.assertIn('-f ref="$BASE_REF"', text)
        self.assertIn('-f ref="$HEAD_REF"', text)
        self.assertIn("Integration dispatched: %s", text)
        self.assertIn("COMMENT_BODY", text)
        self.assertIn(
            "printf 'Merged by repository policy: `%s -> %s`",
            text,
        )

    def test_cleanup_command_is_owner_only_and_keeps_unmerged_branches(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("github.event.comment.body == '/cleanup-branches'", text)
        self.assertIn("github.actor == github.repository_owner", text)
        self.assertIn("github.event.issue.number == 481", text)
        self.assertIn("gh pr list", text)
        self.assertIn("--state open", text)
        self.assertIn("pulls?state=closed&per_page=100", text)
        self.assertIn("select(.merged_at != null) | .head.ref", text)
        self.assertIn("is_merged_pr_head", text)
        self.assertIn("closed_issue_number", text)
        self.assertIn(r"^issue/([0-9]+)-", text)
        self.assertIn('repos/$REPOSITORY/issues/$number', text)
        self.assertIn('[ "$state" = "closed" ]', text)
        self.assertIn("scripts/merge_policy.py", text)
        self.assertIn("--base __cleanup__", text)
        self.assertIn("compare/$encoded...$target", text)
        self.assertIn('"ahead"', text)
        self.assertIn('"identical"', text)
        self.assertIn(
            "Deleted integrated or squash-merged temporary branches",
            text,
        )
        self.assertIn(
            "Retired unique branches owned by closed issues",
            text,
        )
        self.assertIn("OBSOLETE_HISTORY_BACKUPS", text)
        self.assertIn(
            "backup/dev-cad-before-clean-history-2026-11-21=286923c7db25b5f77dce27e0a7c330cfb44ae3c5",
            text,
        )
        self.assertIn(
            "backup/dev-ci-before-clean-history-2026-11-21=ece7f96ca35afe662aaff4f9ea7e27fed8161049",
            text,
        )
        self.assertIn(
            "backup/main-before-clean-history-2026-11-21=02899ca28457dfb1587bc2bbc3a319cc40a4dfd0",
            text,
        )
        self.assertIn(
            "backup/main-before-final-clean-history-2026-11-21=95cc876a655f784afc518cdb6a0104159f0620a6",
            text,
        )
        self.assertNotIn(
            "backup/gh-pages-before-f11-2026-11-20=",
            text,
        )
        self.assertIn("Retired exact clean-history backup refs", text)
        self.assertIn("Kept because a clean-history backup SHA changed", text)
        self.assertIn("source_branch @ $source_sha", text)
        self.assertIn("Kept because an open PR still uses the branch", text)
        self.assertIn("Kept because unique/unmerged commits remain", text)
        self.assertIn("git/refs/heads/$source_branch", text)

    def test_workflow_does_not_duplicate_branch_policy_literals(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertNotIn('HEAD_REF" = "dev-cad"', text)
        self.assertNotIn('HEAD_REF" = "dev-ci"', text)
        self.assertNotIn('promote/dev-cad', text)
        self.assertNotIn('promote/dev-ci', text)


if __name__ == "__main__":
    unittest.main()
