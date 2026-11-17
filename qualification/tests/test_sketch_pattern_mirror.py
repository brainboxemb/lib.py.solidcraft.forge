"""Q1/Q2 contract for generic associative sketch pattern/mirror handles."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script
from qualification.native_cases import mutation_spec


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/sketch-pattern-mirror/scpf/model.py"


class SketchPatternMirrorQualificationTests(unittest.TestCase):
    def setUp(self):
        self.document = run_script(MODEL)
        self.commands = self.document["commands"]
        self.names = [command["command"] for command in self.commands]

    def test_circle_seed_stays_one_native_profile_with_pattern_and_mirror(self):
        self.assertEqual(self.names.count("sketch.circle.center"), 1)
        self.assertEqual(self.names.count("sketch.pattern.rectangular"), 2)
        self.assertEqual(self.names.count("sketch.mirror"), 4)

        circle = next(
            command for command in self.commands
            if command["command"] == "sketch.circle.center"
        )
        self.assertEqual(circle["params"]["diameter"], "hole_diameter")
        self.assertIn("bind", circle)

        patterns = [
            command for command in self.commands
            if command["command"] == "sketch.pattern.rectangular"
        ]
        dog_pattern = patterns[0]
        self.assertEqual(dog_pattern["params"]["count"], "hole_columns")
        self.assertEqual(dog_pattern["params"]["spacing"], "hole_pitch")
        self.assertEqual(dog_pattern["params"]["dir"], [1.0, 0.0])
        self.assertIn("bind", dog_pattern)

        mirrors = [
            command for command in self.commands
            if command["command"] == "sketch.mirror"
        ]
        self.assertEqual(mirrors[0]["params"]["line"], "x")

    def test_slot_seed_stays_one_native_profile_with_pattern_and_mirrors(self):
        self.assertEqual(self.names.count("sketch.slot.center_to_center"), 1)
        slot = next(
            command for command in self.commands
            if command["command"] == "sketch.slot.center_to_center"
        )
        self.assertEqual(slot["params"]["p0"], [20, 20])
        self.assertEqual(slot["params"]["p1"], [40, 20])
        self.assertEqual(slot["params"]["width"], 8.0)
        self.assertIn("bind", slot)

        patterns = [
            command for command in self.commands
            if command["command"] == "sketch.pattern.rectangular"
        ]
        clamp_pattern = patterns[1]
        self.assertEqual(clamp_pattern["params"]["count"], "slot_count")
        self.assertEqual(clamp_pattern["params"]["spacing"], "slot_pitch")
        self.assertEqual(clamp_pattern["params"]["dir"], [1.0, 0.0])

        mirrors = [
            command for command in self.commands
            if command["command"] == "sketch.mirror"
        ]
        self.assertEqual(
            [command["params"]["line"] for command in mirrors],
            ["x", "y", "x", "x"],
        )

    def test_one_sketch_and_cut_per_profile_family(self):
        self.assertEqual(self.names.count("sketch.create"), 2)
        self.assertEqual(self.names.count("sketch.finish"), 2)
        self.assertEqual(self.names.count("solid.extrude"), 2)
        self.assertEqual(self.names.count("model.faces"), 2)

    def test_pattern_parameters_have_correct_native_units(self):
        units = {
            command["params"]["name"]: command["params"]["unit"]
            for command in self.commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(units["hole_diameter"], "mm")
        self.assertEqual(units["hole_columns"], "")
        self.assertEqual(units["hole_pitch"], "mm")
        self.assertEqual(units["slot_count"], "")
        self.assertEqual(units["slot_pitch"], "mm")

    def test_saved_design_mutation_changes_seed_and_pattern_parameters(self):
        spec = mutation_spec("sketch-pattern-mirror")
        self.assertIsNotNone(spec)
        document = json.loads(
            (ROOT / spec["command"]).read_text(encoding="utf-8")
        )
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(
            changes,
            {
                "hole_diameter": "10 mm",
                "hole_columns": "3",
                "hole_pitch": "30 mm",
                "slot_count": "3",
                "slot_pitch": "30 mm",
            },
        )


if __name__ == "__main__":
    unittest.main()
