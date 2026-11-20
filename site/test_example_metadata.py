#!/usr/bin/env python3
"""Validate self-describing Forge example metadata."""

from __future__ import annotations

from pathlib import Path
import unittest

from example_metadata import discover_example_metadata


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
                self.assertGreaterEqual(len(row.concepts), 1)
                self.assertGreaterEqual(len(row.verification_proves), 1)

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
