"""Command contract for the native profile-driven Revolve fixture."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "models/native-revolve"
MODEL = EXAMPLE / "scpf/model.py"
MUTATION = EXAMPLE / "verification/change_geometry.json"


class NativeRevolveContractTests(unittest.TestCase):
    def setUp(self):
        self.commands = run_script(MODEL)["commands"]

    def test_emits_one_native_revolve_feature(self):
        revolves = [
            row for row in self.commands
            if row["command"] == "solid.revolve"
        ]
        self.assertEqual(len(revolves), 1)
        self.assertEqual(
            revolves[0]["params"],
            {
                "sketch": "RadialProfile",
                "axis": "X",
                "angle": "sweep",
                "body_name": "NativeRevolve",
            },
        )
        self.assertFalse(
            any(row["command"] == "solid.extrude" for row in self.commands)
        )

    def test_revolve_parameters_keep_length_and_angle_units(self):
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in self.commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["length"], "mm")
        self.assertEqual(units["radius"], "mm")
        self.assertEqual(units["sweep"], "deg")

    def test_saved_design_mutates_radius_and_sweep(self):
        document = json.loads(MUTATION.read_text(encoding="utf-8"))
        changes = {
            row["params"]["name"]: row["params"]["expression"]
            for row in document["commands"]
        }
        self.assertEqual(
            changes,
            {
                "radius": "5 mm",
                "sweep": "180 deg",
            },
        )


if __name__ == "__main__":
    unittest.main()
