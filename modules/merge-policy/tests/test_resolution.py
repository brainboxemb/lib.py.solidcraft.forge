import unittest

from cad_model_merge_policy.resolution import (
    parse_resolution_command,
    verify_merge_object,
)


class ResolutionTests(unittest.TestCase):
    def command(self):
        return "\n".join(
            [
                "/merge-resolved",
                "base " + "a" * 40,
                "head " + "b" * 40,
                "resolution-pr 42",
                "resolution resolve/42-dev-exp " + "c" * 40 + " " + "d" * 40,
            ]
        )

    def test_parser_binds_exact_reviewed_evidence(self):
        value = parse_resolution_command(self.command())
        self.assertEqual(value.base_sha, "a" * 40)
        self.assertEqual(value.head_sha, "b" * 40)
        self.assertEqual(value.resolution_pr, 42)
        self.assertEqual(value.resolution_ref, "resolve/42-dev-exp")
        self.assertEqual(value.resolution_sha, "c" * 40)
        self.assertEqual(value.resolution_tree, "d" * 40)

    def test_parser_rejects_wrong_prefix_or_non_exact_sha(self):
        with self.assertRaisesRegex(ValueError, "configured prefix"):
            parse_resolution_command(
                self.command().replace("resolve/42-dev-exp", "sync/42-dev-exp")
            )
        with self.assertRaisesRegex(ValueError, "40-character"):
            parse_resolution_command(
                self.command().replace("base " + "a" * 40, "base abc")
            )

    def test_parser_rejects_missing_or_extra_fields(self):
        with self.assertRaises(ValueError):
            parse_resolution_command("/merge-resolved")
        with self.assertRaises(ValueError):
            parse_resolution_command(self.command() + "\nextra value")

    def test_merge_object_requires_exact_tree_and_parent_order(self):
        payload = {
            "sha": "e" * 40,
            "tree": {"sha": "d" * 40},
            "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
        }
        self.assertEqual(
            verify_merge_object(
                payload,
                expected_tree="d" * 40,
                expected_parents=("a" * 40, "b" * 40),
            ),
            "e" * 40,
        )

        reversed_parents = dict(payload)
        reversed_parents["parents"] = [
            {"sha": "b" * 40},
            {"sha": "a" * 40},
        ]
        with self.assertRaisesRegex(ValueError, "parents mismatch"):
            verify_merge_object(
                reversed_parents,
                expected_tree="d" * 40,
                expected_parents=("a" * 40, "b" * 40),
            )


if __name__ == "__main__":
    unittest.main()
