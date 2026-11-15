"""Affected-case selection stays deterministic and explicit."""

import unittest

from qualification.case_selection import CASE_SLUGS, parse_case_selection


class CaseSelectionTests(unittest.TestCase):
    def test_all_selects_registry_order(self):
        self.assertEqual(parse_case_selection("all"), CASE_SLUGS)
        self.assertEqual(parse_case_selection(None), CASE_SLUGS)

    def test_single_case(self):
        self.assertEqual(
            parse_case_selection("four-corner-l"),
            ("four-corner-l",),
        )

    def test_multiple_cases_keep_registry_order(self):
        selected = parse_case_selection(
            "xz-anchor, components four-corner-l"
        )
        self.assertEqual(
            selected,
            ("components", "four-corner-l", "xz-anchor"),
        )

    def test_group_expands_to_registered_cases(self):
        selected = parse_case_selection("group:anchors")
        self.assertIn("corner-anchor", selected)
        self.assertIn("anchor-topology-mutation", selected)
        self.assertIn("four-corner-l", selected)
        self.assertNotIn("simple-box", selected)

    def test_duplicate_tokens_do_not_duplicate_cases(self):
        self.assertEqual(
            parse_case_selection("components,components"),
            ("components",),
        )

    def test_unknown_case_fails(self):
        with self.assertRaisesRegex(ValueError, "unknown qualification case"):
            parse_case_selection("does-not-exist")

    def test_unknown_group_fails(self):
        with self.assertRaisesRegex(ValueError, "unknown qualification group"):
            parse_case_selection("group:does-not-exist")


if __name__ == "__main__":
    unittest.main()
