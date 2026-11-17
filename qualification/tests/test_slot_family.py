"""Qualification contract for the five native Slot creators."""
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/slot-family/scpf/model.py"


class SlotFamilyQualificationTests(unittest.TestCase):
    def test_slot_family_command_contract(self):
        commands = run_script(MODEL)["commands"]
        native = [
            command["command"]
            for command in commands
            if command["command"].startswith("sketch.slot.")
        ]
        self.assertEqual(
            native,
            [
                "sketch.slot.center_to_center",
                "sketch.slot.overall",
                "sketch.slot.center_point",
                "sketch.slot.arc_three_point",
                "sketch.slot.arc_center",
            ],
        )
        self.assertNotIn(
            "sketch.rectangle.rounded",
            [command["command"] for command in commands],
        )

        extrude = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.extrude"
        )
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")
        self.assertEqual(extrude["operation"], "cut")
        self.assertNotIn("distance", extrude)


if __name__ == "__main__":
    unittest.main()
