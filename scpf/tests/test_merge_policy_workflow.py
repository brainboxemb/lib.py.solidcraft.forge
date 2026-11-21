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
        self.assertIn("git/refs/heads/$HEAD_REF", text)
        self.assertIn("temporary head deleted", text)
        self.assertIn("long-lived lane recreated at merge commit", text)
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
        self.assertIn("scripts/merge_policy.py", text)
        self.assertIn("--base __cleanup__", text)
        self.assertIn("compare/$encoded...$target", text)
        self.assertIn('"ahead"', text)
        self.assertIn('"identical"', text)
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
