"""PR verification scope delegates case and target-stage policy to impact.py."""

import unittest

from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS
from qualification.preview_scope import (
    affected_cases,
    reference_smoke_reasons,
    reference_smoke_required,
    target_stage,
)


class PreviewScopeTests(unittest.TestCase):
    def test_site_change_needs_no_model_case(self):
        paths = ["site/build.py", "site/style.css"]
        self.assertEqual(affected_cases(paths), ())
        self.assertEqual(target_stage(paths, ()), "none")
        self.assertFalse(reference_smoke_required(paths))

    def test_direct_example_change_selects_model_verify(self):
        paths = ["examples/slot-family/scpf/model.py"]
        cases = affected_cases(paths)
        self.assertEqual(cases, ("slot-family",))
        self.assertEqual(target_stage(paths, cases), "model_verify")

    def test_example_test_selects_its_case(self):
        cases = affected_cases(["examples/slot-family/tests/test_contract.py"])
        self.assertEqual(cases, ("slot-family",))

    def test_foundational_forge_change_requires_tool_qualification(self):
        paths = ["scpf/scpf/replay.py"]
        cases = affected_cases(paths)
        self.assertTrue(cases)
        self.assertEqual(target_stage(paths, cases), "tool_qualification")

    def test_global_case_registry_change_selects_all_cases(self):
        cases = affected_cases(["qualification/cases.py"])
        self.assertGreater(len(cases), 10)

    def test_reference_validation_requires_reference_verification(self):
        paths = ["qualification/reference_validation.py"]
        self.assertTrue(reference_smoke_required(paths))
        self.assertEqual(reference_smoke_reasons(paths), tuple(paths))

    def test_each_registered_reference_directory_requires_verification(self):
        for implementation in DEFAULT_REFERENCE_IMPLEMENTATIONS:
            with self.subTest(implementation=implementation):
                self.assertTrue(
                    reference_smoke_required(
                        [f"examples/simple-box/{implementation}/model.py"]
                    )
                )

    def test_toolchain_change_requires_reference_verification(self):
        self.assertTrue(
            reference_smoke_required(["qualification/toolchain.json"])
        )

    def test_normal_docs_skip_reference_verification(self):
        self.assertFalse(
            reference_smoke_required(
                ["docs/05-cad-api-design.md", "CHANGELOG.md"]
            )
        )


if __name__ == "__main__":
    unittest.main()
