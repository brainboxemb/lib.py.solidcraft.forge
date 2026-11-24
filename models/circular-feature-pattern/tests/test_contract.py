"""Integration contract for native circular feature patterns."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "models/circular-feature-pattern"
MODEL = EXAMPLE / "scpf/model.py"
MUTATION = EXAMPLE / "verification/change_count.json"


class CircularFeaturePatternContractTests(unittest.TestCase):
    def setUp(self):
        self.commands = run_script(MODEL)["commands"]

    def test_emits_one_native_circular_feature_pattern(self):
        patterns = [
            command for command in self.commands
            if command["command"] == "solid.pattern.circular"
        ]
        self.assertEqual(len(patterns), 1)
        self.assertEqual(
            patterns[0]["params"],
            {
                "features": ["Hole1"],
                "axis": "Z",
                "count": "bolts",
                "alignment": "right",
                "reversed": False,
            },
        )

    def test_count_parameter_is_dimensionless_and_pcd_is_length(self):
        units = {
            command["params"]["name"]: command["params"]["unit"]
            for command in self.commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(units["bolts"], "")
        self.assertEqual(units["pcd"], "mm")

    def test_source_hole_is_one_direct_native_feature(self):
        self.assertEqual(
            [row["command"] for row in self.commands].count("solid.hole"),
            1,
        )
        self.assertFalse(
            any(row["command"] == "solid.extrude" for row in self.commands)
        )
        self.assertFalse(
            any(row["command"] == "sketch.create" for row in self.commands)
        )

    def test_saved_design_mutation_changes_pattern_count(self):
        document = json.loads(MUTATION.read_text(encoding="utf-8"))
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(changes, {"bolts": "4"})


if __name__ == "__main__":
    unittest.main()
