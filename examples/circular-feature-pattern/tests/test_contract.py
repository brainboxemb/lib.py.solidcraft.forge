"""Integration contract for native circular feature patterns."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples/circular-feature-pattern"
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
                "features": ["BoltHole"],
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

    def test_source_cut_is_not_expanded_in_python(self):
        self.assertEqual(
            [row["command"] for row in self.commands].count("solid.extrude"),
            1,
        )
        self.assertEqual(
            [row["command"] for row in self.commands].count(
                "sketch.circle.center"
            ),
            1,
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
