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
            REQUIRED_LEVEL["affected-q1-q2"],
            "affected-q1-q2",
        )
        self.assertEqual(
            REQUIRED_LEVEL["affected-q1-q6"],
            "affected-q1-q6",
        )
        self.assertEqual(
            REQUIRED_LEVEL["full-q1-q6"],
            "q1-q6-full",
        )
        self.assertNotIn("preflight", REQUIRED_LEVEL)


if __name__ == "__main__":
    unittest.main()
