"""integration contract for native circular feature patterns."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script
from qualification.cases import QUALIFICATION_CASES
from qualification.native_cases import mutation_spec


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples/circular-feature-pattern/scpf/model.py"


class CircularFeaturePatternQualificationTests(unittest.TestCase):
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

    def test_saved_design_mutates_pattern_count_in_saved_design(self):
        case = next(
            case for case in QUALIFICATION_CASES
            if case["slug"] == "circular-feature-pattern"
        )
        self.assertTrue(case["saved_design_required"])

        spec = mutation_spec("circular-feature-pattern")
        self.assertIsNotNone(spec)
        document = json.loads(
            (ROOT / spec["command"]).read_text(encoding="utf-8")
        )
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(changes, {"bolts": "4"})


if __name__ == "__main__":
    unittest.main()
