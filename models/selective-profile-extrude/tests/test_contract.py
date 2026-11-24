"""Integration contract for selective Sketch profile extrusion."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "models/selective-profile-extrude"
MODEL = EXAMPLE / "scpf/model.py"
MUTATION = EXAMPLE / "verification/change_pattern.json"


class SelectiveProfileExtrudeContractTests(unittest.TestCase):
    def setUp(self):
        self.document = run_script(MODEL)
        self.commands = self.document["commands"]

    def test_one_pattern_and_one_selective_native_extrusion(self):
        names = [row["command"] for row in self.commands]
        self.assertEqual(names.count("sketch.circle.center"), 1)
        self.assertEqual(names.count("sketch.pattern.rectangular"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)

        pattern = next(
            row for row in self.commands
            if row["command"] == "sketch.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["count"], 4)
        self.assertEqual(pattern["params"]["spacing"], "hole_pitch")

        extrude = next(
            row["params"]
            for row in self.commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(
            extrude["profiles"],
            [
                {"point": [-30.0, 0.0]},
                {"point": [-10.0, 0.0]},
                {"point": [30.0, 0.0]},
            ],
        )
        self.assertTrue(extrude["exact_regions"])
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")

    def test_saved_design_mutation_changes_seed_and_pattern_spacing(self):
        document = json.loads(MUTATION.read_text(encoding="utf-8"))
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(
            changes,
            {
                "hole_diameter": "10 mm",
                "hole_pitch": "24 mm",
            },
        )


if __name__ == "__main__":
    unittest.main()
