"""Q1/Q2 tests for the five native SolidCraft Slot constructors."""
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/slot-family/scpf/model.py"


class NativeSlotFamilyTests(unittest.TestCase):
    def test_all_five_slot_variants_lower_one_to_one(self):
        commands = run_script(MODEL)["commands"]
        slot_commands = [
            command for command in commands
            if command["command"].startswith("sketch.slot.")
        ]
        self.assertEqual(
            [command["command"] for command in slot_commands],
            [
                "sketch.slot.center_to_center",
                "sketch.slot.overall",
                "sketch.slot.center_point",
                "sketch.slot.arc_three_point",
                "sketch.slot.arc_center",
            ],
        )
        self.assertTrue(all(command["params"]["width"] == 8.0
                            for command in slot_commands))
        self.assertEqual(slot_commands[-1]["params"]["sweep"], 120)
        self.assertNotIn(
            "sketch.rectangle.rounded",
            [command["command"] for command in commands],
        )

    def test_slot_family_is_one_editable_sketch_and_cut(self):
        commands = run_script(MODEL)["commands"]
        names = [command["command"] for command in commands]
        self.assertEqual(names.count("sketch.create"), 1)
        self.assertEqual(names.count("sketch.finish"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)
        extrude = next(command for command in commands
                       if command["command"] == "solid.extrude")
        self.assertEqual(extrude["params"]["operation"], "cut")
        self.assertTrue(extrude["params"]["through_all"])

    def test_symbolic_width_is_rejected_by_direct_native_slot_creator(self):
        from scpf import Parameter, SlotCenterToCenter2D
        with self.assertRaisesRegex(TypeError, "sketch.draw.dimensioned"):
            SlotCenterToCenter2D((0, 0), (20, 0), Parameter("width", 8))

    def test_arc_center_requires_one_end_definition(self):
        from scpf import SlotArcCenter2D
        with self.assertRaisesRegex(ValueError, "exactly one"):
            SlotArcCenter2D((0, 0), (10, 0), 4)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            SlotArcCenter2D((0, 0), (10, 0), 4, end=(0, 10), sweep=90)


if __name__ == "__main__":
    unittest.main()
