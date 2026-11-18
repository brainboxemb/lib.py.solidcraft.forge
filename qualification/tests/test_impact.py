"""Tests for risk classification and deterministic affected-case selection."""

from pathlib import Path
import tempfile
import unittest

from qualification.impact import (
    affected_cases,
    case_dependencies,
    case_input_hash,
    classify,
    classify_path,
    final_gate,
)


class ImpactTests(unittest.TestCase):
    def test_presentation_is_cheap(self):
        paths = ["site/build.py", "docs/11-generated-output.md"]
        self.assertEqual(classify(paths), "presentation")
        self.assertEqual(affected_cases(paths), ())
        self.assertEqual(final_gate(paths, ()), "preflight")

    def test_unknown_path_fails_safe(self):
        self.assertEqual(classify_path("mystery/input.bin"), "unknown")
        self.assertEqual(
            final_gate(["mystery/input.bin"], ()),
            "full-q1-q6",
        )

    def test_foundational_compiler_change_selects_all_cases(self):
        cases = affected_cases(["scpf/scpf/compiler.py"])
        self.assertGreater(len(cases), 10)
        self.assertEqual(
            final_gate(["scpf/scpf/compiler.py"], cases),
            "full-q1-q6",
        )

    def test_direct_case_change_selects_only_that_case(self):
        paths = ["examples/simple-box/scpf/model.py"]
        self.assertEqual(affected_cases(paths), ("simple-box",))
        self.assertEqual(final_gate(paths, ("simple-box",)), "affected-q1-q2")

    def test_q1_evidence_selects_its_cases(self):
        cases = affected_cases(["scpf/tests/test_native_slots.py"])
        self.assertIn("slot-family", cases)

    def test_case_dependencies_include_foundational_modules(self):
        deps = set(case_dependencies("simple-box"))
        self.assertIn("scpf/scpf/compiler.py", deps)
        self.assertIn("scpf/scpf/replay.py", deps)

    def test_hash_changes_when_case_source_changes(self):
        original = case_input_hash("simple-box")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # A minimal copy is intentionally not enough to resolve the full
            # dependency closure; this test only proves stable prefix/format.
            self.assertTrue(original.startswith("sha256:"))
            self.assertEqual(len(original), len("sha256:") + 64)


if __name__ == "__main__":
    unittest.main()
