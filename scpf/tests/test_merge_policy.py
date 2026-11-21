from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "scripts" / "merge_policy.py"

spec = importlib.util.spec_from_file_location("merge_policy", POLICY_PATH)
assert spec is not None and spec.loader is not None
merge_policy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = merge_policy
spec.loader.exec_module(merge_policy)


class MergePolicyTests(unittest.TestCase):
    def test_merge_method_matrix(self):
        cases = (
            ("dev-cad", "feature/x", "squash", False),
            ("dev-ci", "feature/x", "squash", False),
            ("main", "issue/592-governance", "squash", False),
            ("main", "promote/dev-cad", "squash", False),
            ("main", "promote/dev-ci", "squash", False),
            ("main", "dev-cad", "merge", True),
            ("main", "dev-ci", "merge", True),
        )
        for base, head, method, promotion in cases:
            with self.subTest(base=base, head=head):
                result = merge_policy.evaluate(base=base, head=head)
                self.assertEqual(result.merge_method, method)
                self.assertEqual(result.direct_lane_promotion, promotion)
                self.assertEqual(
                    result.integrate_base,
                    base in {"main", "dev-cad", "dev-ci"},
                )

    def test_non_durable_base_does_not_request_integration(self):
        result = merge_policy.evaluate(base="experiment", head="feature/x")
        self.assertFalse(result.integrate_base)

    def test_cleanup_allow_list(self):
        for head in (
            "issue/123-example",
            "fix/bug",
            "feature/thing",
            "accept/proof",
            "promote/dev-ci",
            "docs/update",
            "chore/cleanup",
        ):
            with self.subTest(head=head):
                self.assertTrue(merge_policy.is_cleanup_eligible(head))

    def test_permanent_and_unknown_refs_are_never_cleanup_eligible(self):
        for head in (
            "main",
            "dev-cad",
            "dev-ci",
            "build",
            "gh-pages",
            "backup/gh-pages-before-cutover",
            "release/0.12.0",
            "someone-unexpected",
        ):
            with self.subTest(head=head):
                self.assertFalse(merge_policy.is_cleanup_eligible(head))

    def test_direct_lane_promotion_never_requests_head_cleanup(self):
        for head in ("dev-cad", "dev-ci"):
            result = merge_policy.evaluate(base="main", head=head)
            self.assertTrue(result.direct_lane_promotion)
            self.assertFalse(result.cleanup_head)


if __name__ == "__main__":
    unittest.main()
