"""Tests for merge promotion safety."""

import inspect
import unittest

from scripts.merge_promotion import REQUIRED_LEVEL, prepare


class MergePromotionTests(unittest.TestCase):
    def test_promotion_requires_current_main_identity(self):
        self.assertIn(
            "current_main_sha",
            inspect.signature(prepare).parameters,
        )

    def test_promotion_levels_use_explicit_verification_stages(self):
        self.assertEqual(REQUIRED_LEVEL["tool_verify"], "tool_verify")
        self.assertEqual(REQUIRED_LEVEL["model_verify"], "model_verify")
        self.assertEqual(
            REQUIRED_LEVEL["tool_qualification"],
            "tool_qualification",
        )
        self.assertEqual(REQUIRED_LEVEL["evidence"], "evidence")
        for legacy in (
            "affected-integration",
            "affected-native",
            "full-native",
        ):
            self.assertNotIn(legacy, REQUIRED_LEVEL)


if __name__ == "__main__":
    unittest.main()
