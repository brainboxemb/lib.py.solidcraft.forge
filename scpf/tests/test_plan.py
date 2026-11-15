"""Tests for serializable Forge execution-plan references."""

import unittest

from scpf.plan import (
    binding_specs,
    references_in,
    resolve_references,
    result_ref,
    validate_document,
)


class ExecutionPlanTests(unittest.TestCase):
    def test_result_reference_round_trips_as_plain_json_data(self):
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

    def test_document_binding_must_precede_its_use(self):
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
            ],
        }
        with self.assertRaisesRegex(ValueError, "unknown binding"):
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
        self.assertEqual(
            binding_specs(document),
            {"occurrence:right": (0, "occurrence")},
        )


if __name__ == "__main__":
    unittest.main()
