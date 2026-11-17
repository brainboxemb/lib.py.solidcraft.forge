"""Q1/Q2 contract for native rectangular feature patterns."""
import json
import unittest
from pathlib import Path

from scpf.runner import run_script
from qualification.cases import QUALIFICATION_CASES
from qualification.native_cases import mutation_spec


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/rectangular-pattern/scpf/model.py"


class RectangularPatternQualificationTests(unittest.TestCase):
    def test_emits_one_native_feature_pattern(self):
        commands = run_script(MODEL)["commands"]
        patterns = [
            command for command in commands
            if command["command"] == "solid.pattern.rectangular"
        ]
        self.assertEqual(len(patterns), 1)
        params = patterns[0]["params"]
        self.assertEqual(params["features"], ["Slot"])
        self.assertEqual(params["count1"], "columns")
        self.assertEqual(params["spacing1"], "pitch")
        self.assertEqual(params["count2"], "rows")
        self.assertEqual(params["spacing2"], "row_pitch")

    def test_one_direction_form_omits_second_direction_fields(self):
        commands = run_script(MODEL)["commands"]
        # Reuse the compiled source feature but construct a focused one-row
        # command contract through the public API in the unit-level test.
        from scpf.core import Anchor, Axis, Box, SlotCenterToCenter2D
        from scpf.explicit_sketch import Sketch
        from scpf.compiler import compile_model

        plate = Box(80, 40, 4, anchor=Anchor.BOTTOM)
        with Sketch(name="Slot", on=plate) as slot:
            SlotCenterToCenter2D((-5, 0), (5, 0), 6)
        source = slot.extrude(-4)
        plate = plate - source
        patterned = plate.rectangular_pattern(
            source,
            count=3,
            spacing=20,
            direction=Axis.X,
        )
        pattern = next(
            command for command in compile_model(patterned, "Plate")["commands"]
            if command["command"] == "solid.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["features"], ["Slot"])
        self.assertEqual(pattern["params"]["count1"], 3)
        self.assertEqual(pattern["params"]["spacing1"], 20)
        self.assertNotIn("dir2", pattern["params"])
        self.assertNotIn("count2", pattern["params"])
        self.assertNotIn("spacing2", pattern["params"])

    def test_count_parameters_are_dimensionless(self):
        commands = run_script(MODEL)["commands"]
        params = {
            command["params"]["name"]: command["params"]["unit"]
            for command in commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(params["columns"], "")
        self.assertEqual(params["rows"], "")
        self.assertEqual(params["pitch"], "mm")
        self.assertEqual(params["row_pitch"], "mm")

    def test_q5_is_required_for_native_pattern_parameters(self):
        case = next(
            case for case in QUALIFICATION_CASES
            if case["slug"] == "rectangular-pattern"
        )
        self.assertTrue(case["q5_required"])
        self.assertIn("columns", case["mutation"])
        self.assertIn("pitch", case["mutation"])

    def test_q5_mutation_changes_count_and_spacing(self):
        spec = mutation_spec("rectangular-pattern")
        self.assertIsNotNone(spec)
        command_path = ROOT / spec["command"]
        document = json.loads(command_path.read_text(encoding="utf-8"))
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(
            changes,
            {
                "columns": "2",
                "pitch": "30 mm",
            },
        )

    def test_source_cut_is_not_expanded_in_python(self):
        commands = run_script(MODEL)["commands"]
        self.assertEqual(
            [c["command"] for c in commands].count("solid.extrude"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
