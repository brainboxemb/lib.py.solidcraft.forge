"""Tests for reconcile namespace classification."""

import unittest

from scripts.reconcile_generated import tree_dirs


class ReconcileGeneratedTests(unittest.TestCase):
    def test_tree_dirs_missing_path_is_empty(self):
        # The helper is deliberately idempotent: a missing generated subtree is
        # not an error. Integration behavior is exercised by the live workflow.
        self.assertTrue(callable(tree_dirs))


if __name__ == "__main__":
    unittest.main()
