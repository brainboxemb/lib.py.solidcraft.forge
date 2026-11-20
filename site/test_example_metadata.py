#!/usr/bin/env python3
"""Validate self-describing Forge example metadata."""

from __future__ import annotations

from pathlib import Path
import unittest

from example_metadata import discover_example_metadata
from example_documentation import (
    LEGACY_CASE_SOURCE_COMMIT,
    discover_example_documentation,
)


ROOT = Path(__file__).resolve().parents[1]


class ExampleMetadataTests(unittest.TestCase):
    def test_complete_qualification_catalog_is_self_describing(self):
        rows = discover_example_metadata()
        self.assertEqual(len(rows), 32)

        for row in rows:
            with self.subTest(slug=row.slug):
                root = ROOT / "examples" / row.slug
                self.assertTrue((root / "scpf" / "model.py").is_file())
                self.assertTrue((root / "verification" / "verify.py").is_file())
                self.assertGreaterEqual(len(row.stages), 1)
                self.assertTrue((root / "README.md").is_file())


    def test_preserved_example_documentation_is_complete_and_provenanced(self):
        rows = discover_example_documentation()
        self.assertEqual(len(rows), 32)

        for row in rows:
            with self.subTest(slug=row.slug):
                root = ROOT / "examples" / row.slug
                source = (root / "README.md").read_text(encoding="utf-8")
                self.assertIn(LEGACY_CASE_SOURCE_COMMIT, source)
                self.assertTrue(row.title)
                self.assertTrue(row.group)
                self.assertTrue(row.goal)
                self.assertTrue(row.forge_api)
                self.assertTrue(row.forge_model)
                self.assertTrue(row.lowering)
                self.assertTrue(row.solidcraft_result)
                self.assertTrue(row.saved_design_test)
                self.assertGreaterEqual(len(row.reference_notes), 1)

    def test_model_yml_keeps_only_agreed_generic_fields(self):
        import yaml

        expected = {
            "section",
            "title",
            "tagline",
            "description",
            "parameters",
            "stages",
        }
        for row in discover_example_metadata():
            with self.subTest(slug=row.slug):
                source = (
                    ROOT / "examples" / row.slug / "model.yml"
                ).read_text(encoding="utf-8")
                data = yaml.safe_load(source)
                self.assertEqual(set(data), expected)

    def test_metadata_never_claims_current_verification_status(self):
        forbidden = {"pass", "fail", "passed", "failed", "status"}
        for row in discover_example_metadata():
            with self.subTest(slug=row.slug):
                source = (
                    ROOT / "examples" / row.slug / "model.yml"
                ).read_text(encoding="utf-8").lower()
                for token in forbidden:
                    self.assertNotIn(f"{token}:", source)


if __name__ == "__main__":
    unittest.main()
