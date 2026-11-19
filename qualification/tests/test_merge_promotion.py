"""Tests for merge promotion safety."""

from pathlib import Path
import unittest

from scripts.merge_promotion import REQUIRED_LEVEL


class MergePromotionTests(unittest.TestCase):
    def test_promotion_requires_current_main_identity(self):
        import inspect
        from scripts.merge_promotion import prepare

        self.assertIn(
            "current_main_sha",
            inspect.signature(prepare).parameters,
        )

    def test_final_gate_levels_are_explicit(self):
        self.assertEqual(
            REQUIRED_LEVEL["affected-integration"],
            "affected-integration",
        )
        self.assertEqual(
            REQUIRED_LEVEL["affected-native"],
            "affected-native",
        )
        self.assertEqual(
            REQUIRED_LEVEL["full-native"],
            "full-native",
        )
        self.assertNotIn("preflight", REQUIRED_LEVEL)


if __name__ == "__main__":
    unittest.main()
