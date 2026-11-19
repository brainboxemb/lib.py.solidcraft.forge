"""Regression tests for semantic qualification report rendering."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qualification.report import TEMPLATE, render
from scpf.version import TESTED_SOLIDCRAFT_VERSION


class QualificationReportTemplateTests(unittest.TestCase):
    def test_report_is_rendered_from_external_template(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("$case_rows", template)
        self.assertIn("$image_sections", template)

        result = {
            "schema_version": 5,
            "source_commit": "abc123",
            "forge_version": "0.11.0",
            "solidcraft_version": TESTED_SOLIDCRAFT_VERSION,
            "qualified_at": "2026-11-19T00:00:00Z",
            "cases": {
                "demo": {
                    "title": "Demo case",
                    "status": "pass",
                    "checks": {
                        "integration": {"status": "pass"},
                        "native_model": {"status": "pass"},
                        "geometry": {"status": "pass"},
                        "saved_design": {"status": "not-required"},
                        "visual": {
                            "status": "pass",
                            "images": ["model.png"],
                        },
                    },
                }
            },
        }

        report = render(result)

        self.assertIn("# SCPF Forge qualification", report)
        self.assertIn("abc123", report)
        self.assertIn("0.11.0", report)
        self.assertIn(TESTED_SOLIDCRAFT_VERSION, report)
        self.assertIn("2026-11-19T00:00:00Z", report)
        self.assertIn(
            "| demo | PASS | PASS | PASS | PASS | NOT-REQUIRED | PASS |",
            report,
        )
        self.assertIn("../native/demo/model.png", report)
        for legacy in (" Q1 ", " Q2 ", " Q3 ", " Q4 ", " Q5 ", " Q6 "):
            self.assertNotIn(legacy, report)


if __name__ == "__main__":
    unittest.main()
