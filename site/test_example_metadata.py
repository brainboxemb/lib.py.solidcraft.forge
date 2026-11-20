#!/usr/bin/env python3
"""Validate self-describing Forge example metadata."""

from __future__ import annotations

from pathlib import Path
import unittest

from example_metadata import discover_example_metadata, load_section_presentation
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
                self.assertIsInstance(row.bounds_sufficient, bool)
                self.assertTrue(row.geometry_reason)
                self.assertGreaterEqual(len(row.reference_notes), 1)

    def test_bracket_readme_describes_current_minimal_l_profile(self):
        root = ROOT / "examples" / "bracket"
        source = (root / "README.md").read_text(encoding="utf-8")
        documentation = {
            row.slug: row
            for row in discover_example_documentation()
        }["bracket"]

        self.assertIn("# Minimal L-profile", source)
        self.assertIn("**Group:** `fundamentals`", source)
        self.assertEqual(documentation.title, "Minimal L-profile")
        self.assertEqual(documentation.group, "fundamentals")
        self.assertNotIn("two mounting holes", source)
        self.assertNotIn("valid fillet point", source)
        self.assertNotIn("source/bracket.json", source)

    def test_model_yml_keeps_only_agreed_generic_fields(self):
        import yaml

        expected = {
            "section",
            "priority",
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

    def test_section_and_example_priorities_are_complete_and_deterministic(self):
        rows = discover_example_metadata()
        sections = load_section_presentation()

        self.assertEqual(
            set(sections),
            {row.section for row in rows},
        )
        self.assertEqual(
            len({priority for priority, _label, _description in sections.values()}),
            len(sections),
        )

        by_section = {}
        for row in rows:
            self.assertGreater(row.priority, 0)
            by_section.setdefault(row.section, []).append(row)

        for section, section_rows in by_section.items():
            with self.subTest(section=section):
                priorities = [row.priority for row in section_rows]
                self.assertEqual(len(priorities), len(set(priorities)))

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
