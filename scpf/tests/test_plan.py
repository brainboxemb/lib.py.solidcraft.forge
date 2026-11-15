"""Tests for serializable Forge execution references."""

import unittest

from scpf.plan import (
    binding_specs,
    references_in,
    requires_runtime_binding,
    resolve_references,
    result_ref,
    validate_document,
)


class ExecutionPlanTests(unittest.TestCase):
    def test_reference_round_trips_as_plain_json_data(self):
        ref = result_ref("occurrence:right")

        self.assertEqual(ref, {"$ref": "occurrence:right"})
        self.assertEqual(
            references_in({"occurrence": ref, "nested": [1, ref]}),
            {"occurrence:right"},
        )
        self.assertEqual(
            resolve_references(
                {"occurrence": ref},
                {"occurrence:right": 42},
            ),
            {"occurrence": 42},
        )

    def test_raw_document_requires_no_runtime_binding(self):
        document = {
            "commands": [
                {"command": "solid.box", "params": {"width": 10}}
            ]
        }

        self.assertIs(validate_document(document), document)
        self.assertFalse(requires_runtime_binding(document))
        self.assertEqual(binding_specs(document), {})

    def test_binding_must_precede_use(self):
        document = {
            "commands": [
                {
                    "command": "occurrence.move",
                    "params": {
                        "occurrence": result_ref("occurrence:right"),
                    },
                },
                {
                    "command": "occurrence.copy",
                    "params": {"component": "Block"},
                },
            ],
            "bindings": {
                "occurrence:right": {
                    "command": 1,
                    "field": "occurrence",
                },
            },
        }

        with self.assertRaisesRegex(ValueError, "before"):
            validate_document(document)

    def test_unknown_binding_is_rejected(self):
        document = {
            "commands": [
                {
                    "command": "occurrence.move",
                    "params": {"occurrence": result_ref("missing")},
                },
            ]
        }

        with self.assertRaisesRegex(ValueError, "unknown binding"):
            validate_document(document)

    def test_unused_binding_is_rejected(self):
        document = {
            "commands": [
                {"command": "occurrence.copy", "params": {"component": "Block"}}
            ],
            "bindings": {
                "occurrence:right": {
                    "command": 0,
                    "field": "occurrence",
                }
            },
        }

        with self.assertRaisesRegex(ValueError, "unused"):
            validate_document(document)

    def test_binding_specs_are_normalized(self):
        document = {
            "commands": [
                {
                    "command": "occurrence.copy",
                    "params": {"component": "Block"},
                },
                {
                    "command": "occurrence.move",
                    "params": {
                        "occurrence": result_ref("occurrence:right"),
                    },
                },
            ],
            "bindings": {
                "occurrence:right": {
                    "command": 0,
                    "field": "occurrence",
                },
            },
        }

        self.assertIs(validate_document(document), document)
        self.assertTrue(requires_runtime_binding(document))
        self.assertEqual(
            binding_specs(document),
            {"occurrence:right": (0, "occurrence")},
        )

    def test_reference_object_must_be_exact(self):
        with self.assertRaisesRegex(ValueError, "only"):
            references_in({"$ref": "occurrence:right", "fallback": 3})


if __name__ == "__main__":
    unittest.main()
