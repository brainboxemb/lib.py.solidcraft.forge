"""Tests for deterministic Forge impact and target-stage selection."""

from pathlib import Path
import tempfile
import unittest

from qualification.impact import (
    affected_cases,
    case_dependencies,
    case_input_hash,
    classify,
    classify_path,
    target_stage,
)


class ImpactTests(unittest.TestCase):
    def test_presentation_needs_no_tool_stage(self):
        paths = ["site/build.py", "docs/11-generated-output.md"]
        self.assertEqual(classify(paths), "presentation")
        self.assertEqual(affected_cases(paths), ())
        self.assertEqual(target_stage(paths, ()), "none")

    def test_unknown_path_fails_safe_to_tool_qualification(self):
        self.assertEqual(classify_path("mystery/input.bin"), "unknown")
        self.assertEqual(
            target_stage(["mystery/input.bin"], ()),
            "tool_qualification",
        )

    def test_foundational_compiler_change_selects_all_cases_and_qualification(self):
        cases = affected_cases(["scpf/scpf/compiler.py"])
        self.assertGreater(len(cases), 10)
        self.assertEqual(
            target_stage(["scpf/scpf/compiler.py"], cases),
            "tool_qualification",
        )

    def test_direct_forge_example_change_selects_model_verify(self):
        paths = ["examples/simple-box/scpf/model.py"]
        self.assertEqual(affected_cases(paths), ("simple-box",))
        self.assertEqual(
            target_stage(paths, ("simple-box",)),
            "model_verify",
        )

    def test_reference_example_change_selects_tool_verify(self):
        paths = ["examples/simple-box/cadquery/model.py"]
        self.assertEqual(affected_cases(paths), ("simple-box",))
        self.assertEqual(
            target_stage(paths, ("simple-box",)),
            "tool_verify",
        )

    def test_example_test_change_selects_its_case(self):
        cases = affected_cases(["examples/slot-family/tests/test_contract.py"])
        self.assertIn("slot-family", cases)

    def test_case_dependencies_include_foundational_modules(self):
        deps = set(case_dependencies("simple-box"))
        self.assertIn("scpf/scpf/compiler.py", deps)
        self.assertIn("scpf/scpf/replay.py", deps)

    def test_case_hash_has_stable_sha256_shape(self):
        original = case_input_hash("simple-box")
        with tempfile.TemporaryDirectory():
            self.assertTrue(original.startswith("sha256:"))
            self.assertEqual(len(original), len("sha256:") + 64)


if __name__ == "__main__":
    unittest.main()
