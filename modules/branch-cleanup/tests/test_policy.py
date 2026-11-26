import unittest

from cad_model_branch_cleanup.config import CleanupConfig
from cad_model_branch_cleanup.policy import (
    eligible_post_merge,
    eligible_sweep,
    is_temporary,
    merge_target,
)


CONFIG = CleanupConfig(
    stable="main",
    development="dev",
    temporary_prefixes=("issue/", "fix/", "feature/", "docs/", "chore/", "release/"),
)


class PolicyTests(unittest.TestCase):
    def test_permanent_branches_are_never_temporary(self):
        self.assertFalse(is_temporary("main", CONFIG))
        self.assertFalse(is_temporary("dev", CONFIG))

    def test_experimental_cleanup(self):
        self.assertFalse(is_temporary("exp", CONFIG))
        self.assertTrue(eligible_post_merge(head="feature/190-work", base="exp", same_repository=True, merged=True, config=CONFIG))
        self.assertFalse(eligible_post_merge(head="release/v1", base="exp", same_repository=True, merged=True, config=CONFIG))
        self.assertFalse(eligible_post_merge(head="exp", base="dev", same_repository=True, merged=True, config=CONFIG))

    def test_allowed_prefix_is_temporary(self):
        self.assertTrue(is_temporary("issue/11-cleanup", CONFIG))

    def test_merged_same_repo_feature_to_dev_is_eligible(self):
        self.assertTrue(
            eligible_post_merge(
                head="fix/7-cleanup",
                base="dev",
                same_repository=True,
                merged=True,
                config=CONFIG,
            )
        )

    def test_release_branch_targets_stable(self):
        self.assertTrue(is_temporary("release/v1.2.3", CONFIG))
        self.assertEqual(merge_target("release/v1.2.3", CONFIG), "main")
        self.assertEqual(merge_target("issue/11-work", CONFIG), "dev")
        self.assertTrue(
            eligible_post_merge(
                head="release/v1.2.3",
                base="main",
                same_repository=True,
                merged=True,
                config=CONFIG,
            )
        )
        self.assertFalse(
            eligible_post_merge(
                head="release/v1.2.3",
                base="dev",
                same_repository=True,
                merged=True,
                config=CONFIG,
            )
        )

    def test_unmerged_or_open_work_is_not_sweep_eligible(self):
        self.assertFalse(
            eligible_sweep(
                branch="issue/11-work",
                has_open_pr=True,
                has_merged_pr_to_target=True,
                config=CONFIG,
            )
        )
        self.assertFalse(
            eligible_sweep(
                branch="issue/12-unmerged",
                has_open_pr=False,
                has_merged_pr_to_target=False,
                config=CONFIG,
            )
        )


if __name__ == "__main__":
    unittest.main()
