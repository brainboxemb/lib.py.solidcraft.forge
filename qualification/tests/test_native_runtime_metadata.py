"""Selected native qualification metadata must cover every Q5 case."""

from pathlib import Path
import re
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

    def test_expectation_dict_literals_have_no_duplicate_keys(self):
        import ast

        source_path = ROOT / "qualification" / "expectations.py"
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant)
                and isinstance(key.value, str)
            ]
            self.assertEqual(
                len(keys),
                len(set(keys)),
                f"duplicate dictionary key in {source_path}: {keys}",
            )

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
        documented_versions = set(
            re.findall(r"SolidCraft (\\d+\\.\\d+\\.\\d+)", text)
        )
        self.assertLessEqual(
            documented_versions,
            {TESTED_SOLIDCRAFT_VERSION},
        )


if __name__ == "__main__":
    unittest.main()
