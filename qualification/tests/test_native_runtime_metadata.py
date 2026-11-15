"""Selected native qualification metadata must cover every Q5 case."""

from pathlib import Path
import unittest

from qualification.case_selection import CASE_SLUGS
from qualification.cases import QUALIFICATION_CASES, QUALIFICATION_LEVELS
from qualification.native_cases import (
    MUTATIONS,
    POST_BUILD_INSPECTIONS,
    q5_required_cases,
    validate_runtime_metadata,
)
from qualification.native_validation import VALIDATORS
from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]


class NativeRuntimeMetadataTests(unittest.TestCase):
    def test_every_case_has_native_validator(self):
        self.assertEqual(set(VALIDATORS), set(CASE_SLUGS))

    def test_every_q5_case_has_one_reusable_mutation(self):
        self.assertEqual(set(MUTATIONS), set(q5_required_cases()))
        validate_runtime_metadata()
        for slug, spec in MUTATIONS.items():
            with self.subTest(case=slug):
                self.assertTrue((ROOT / spec["command"]).is_file())
                self.assertTrue(spec["save"].endswith(".sc"))
                self.assertTrue(spec["measurements"].endswith(".json"))
                self.assertTrue(spec["label"])

    def test_post_build_inspections_reference_real_commands(self):
        for slug, spec in POST_BUILD_INSPECTIONS.items():
            with self.subTest(case=slug):
                self.assertIn(slug, CASE_SLUGS)
                self.assertTrue((ROOT / spec["command"]).is_file())
                self.assertTrue(spec["output"].endswith(".json"))

    def test_documented_native_version_uses_forge_target(self):
        q3 = next(row for row in QUALIFICATION_LEVELS if row[0] == "Q3")
        self.assertIn(f"SolidCraft {TESTED_SOLIDCRAFT_VERSION}", q3[2])

        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for item in value.values():
                    yield from strings(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    yield from strings(item)

        text = "\n".join(strings(QUALIFICATION_CASES))
        self.assertNotIn("SolidCraft 0.30.1", text)


if __name__ == "__main__":
    unittest.main()
