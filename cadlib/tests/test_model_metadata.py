"""Canonical model.yml contract tests."""

import unittest

from scpf.model_metadata import (
    MODEL_METADATA_FIELDS,
    ModelMetadata,
    validate_model_metadata,
)


VALID = {
    "purpose": "verification",
    "section": "basic",
    "priority": 10,
    "title": "Plate",
    "tagline": "A simple plate",
    "description": "One human-facing model description.",
    "parameters": "40 × 20 × 4 mm",
    "stages": ["Create profile", "Extrude"],
}


class ModelMetadataTests(unittest.TestCase):
    def test_canonical_field_set_is_exact(self):
        self.assertEqual(
            MODEL_METADATA_FIELDS,
            (
                "purpose",
                "section",
                "priority",
                "title",
                "tagline",
                "description",
                "parameters",
                "stages",
            ),
        )

    def test_valid_mapping_returns_typed_metadata(self):
        row = validate_model_metadata(VALID, label="plate")
        self.assertIsInstance(row, ModelMetadata)
        self.assertEqual(row.purpose, ("verification",))
        self.assertEqual(row.priority, 10)
        self.assertEqual(row.stages, ("Create profile", "Extrude"))

    def test_purpose_scalar_and_list_forms_normalize(self):
        example = validate_model_metadata(dict(VALID, purpose="example"))
        both = validate_model_metadata(
            dict(VALID, purpose=["verification", "example"])
        )
        self.assertEqual(example.purpose, ("example",))
        self.assertEqual(both.purpose, ("example", "verification"))

    def test_invalid_purpose_is_rejected(self):
        for value in ([], "", "other", ["verification", "verification"]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_model_metadata(dict(VALID, purpose=value))

    def test_unknown_consumer_extension_is_rejected(self):
        data = dict(VALID, build={"process": True})
        with self.assertRaisesRegex(ValueError, "unsupported fields: build"):
            validate_model_metadata(data)

    def test_missing_field_is_rejected(self):
        data = dict(VALID)
        del data["tagline"]
        with self.assertRaisesRegex(ValueError, "missing required fields: tagline"):
            validate_model_metadata(data)

    def test_text_and_stage_values_must_be_non_empty(self):
        for field in ("section", "title", "tagline", "description", "parameters"):
            with self.subTest(field=field):
                data = dict(VALID)
                data[field] = " "
                with self.assertRaises(ValueError):
                    validate_model_metadata(data)

        data = dict(VALID, stages=[])
        with self.assertRaisesRegex(ValueError, "stages must be a non-empty list"):
            validate_model_metadata(data)

    def test_priority_is_a_positive_integer_not_bool(self):
        for value in (0, -1, True, 1.5, "1"):
            with self.subTest(value=value):
                data = dict(VALID, priority=value)
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    validate_model_metadata(data)


if __name__ == "__main__":
    unittest.main()
