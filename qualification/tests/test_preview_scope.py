"""PR verification scope is derived from changed source and proving tests."""

import unittest

from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS
from qualification.preview_scope import (
    affected_cases,
    final_gate,
    reference_smoke_reasons,
    reference_smoke_required,
)


class PreviewScopeTests(unittest.TestCase):
    def test_site_change_needs_no_model_case(self):
        paths = ["site/build.py", "site/style.css"]
        self.assertEqual(affected_cases(paths), ())
        self.assertEqual(final_gate(paths, ()), "preflight")
        self.assertFalse(reference_smoke_required(paths))

    def test_direct_example_change_selects_only_that_case(self):
        paths = ["examples/slot-family/scpf/model.py"]
        cases = affected_cases(paths)
        self.assertEqual(cases, ("slot-family",))
        self.assertEqual(final_gate(paths, cases), "affected-q1-q6")

    def test_q1_test_selects_cases_that_use_it_as_evidence(self):
        cases = affected_cases([
            "scpf/tests/test_native_slots.py",
        ])
        self.assertEqual(cases, ("slot-family",))

    def test_forge_source_requires_a_proving_case(self):
        with self.assertRaisesRegex(ValueError, "without an affected qualification case"):
            affected_cases(["scpf/scpf/explicit_sketch.py"])

    def test_forge_source_with_proving_test_is_scoped(self):
        paths = [
            "scpf/scpf/explicit_sketch.py",
            "scpf/tests/test_native_slots.py",
        ]
        cases = affected_cases(paths)
        self.assertEqual(cases, ("slot-family",))
        self.assertEqual(final_gate(paths, cases), "affected-q1-q6")

    def test_foundational_forge_change_requires_full_final_gate(self):
        paths = [
            "scpf/scpf/replay.py",
            "scpf/tests/test_assembly_placement.py",
        ]
        cases = affected_cases(paths)
        self.assertTrue(cases)
        self.assertEqual(final_gate(paths, cases), "full-q1-q6")

    def test_global_case_registry_change_selects_all_cases(self):
        cases = affected_cases(["qualification/case_evidence.py"])
        self.assertGreater(len(cases), 10)

    def test_preview_scope_code_does_not_install_reference_libraries(self):
        paths = [
            "qualification/preview_scope.py",
            "qualification/tests/test_preview_scope.py",
        ]
        self.assertFalse(reference_smoke_required(paths))

    def test_reference_validation_requires_reference_smoke(self):
        paths = ["qualification/reference_validation.py"]
        self.assertTrue(reference_smoke_required(paths))
        self.assertEqual(reference_smoke_reasons(paths), tuple(paths))

    def test_each_registered_reference_directory_requires_smoke(self):
        for implementation in DEFAULT_REFERENCE_IMPLEMENTATIONS:
            with self.subTest(implementation=implementation):
                self.assertTrue(reference_smoke_required([
                    f"examples/simple-box/{implementation}/model.py",
                ]))

    def test_normal_docs_skip_reference_smoke(self):
        self.assertFalse(reference_smoke_required([
            "docs/05-cad-api-design.md",
            "CHANGELOG.md",
        ]))


if __name__ == "__main__":
    unittest.main()
