"""Q1/Q2 tests for the five native SolidCraft Slot constructors."""
import unittest
from pathlib import Path

from scpf import (
    Box,
    CENTER,
    Depth,
    Parameter,
    Sketch,
    SlotArcCenter2D,
    SlotArcThreePoint2D,
    SlotCenterPoint2D,
    SlotCenterToCenter2D,
    SlotOverall2D,
)
from scpf.compiler import compile_model
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
        self.assertTrue(
            all(command["params"]["width"] == "slot_width"
                for command in slot_commands)
        )
        self.assertEqual(slot_commands[-1]["params"]["sweep"], 120)

        # Plate and Slot width are editable Parameters. Slot-local authored
        # coordinates remain fixed numeric values in this qualification slice.
        point_keys = ("p0", "p1", "center", "end", "start", "through")
        for command in slot_commands:
            for key in point_keys:
                if key not in command["params"]:
                    continue
                self.assertTrue(
                    all(isinstance(value, (int, float))
                        for value in command["params"][key]),
                    (command["command"], key, command["params"][key]),
                )
        self.assertEqual(slot_commands[0]["params"]["p0"], [-60, -35])
        self.assertEqual(slot_commands[0]["params"]["p1"], [-40, -35])

        face_query = next(
            command for command in commands
            if command["command"] == "model.faces"
        )
        self.assertEqual(face_query["params"], {"body": "SlotFamily"})
        self.assertEqual(
            set(face_query["bind"]),
            {"$face_point_1", "$face_index_1"},
        )
        create = next(
            command for command in commands
            if command["command"] == "sketch.create"
        )
        self.assertEqual(
            create["params"]["plane"],
            {
                "face": "$face_point_1",
                "body": "SlotFamily",
                "index": "$face_index_1",
            },
        )
        self.assertFalse(create["params"]["project_edges"])
        self.assertNotIn("offset", create["params"])

        self.assertNotIn(
            "sketch.rectangle.rounded",
            [command["command"] for command in commands],
        )

    def test_slot_family_is_one_editable_sketch_and_cut(self):
        commands = run_script(MODEL)["commands"]
        names = [command["command"] for command in commands]
        self.assertEqual(names.count("model.faces"), 1)
        self.assertEqual(names.count("sketch.create"), 1)
        self.assertEqual(names.count("sketch.finish"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)
        extrude = next(command for command in commands
                       if command["command"] == "solid.extrude")
        self.assertEqual(extrude["params"]["operation"], "cut")
        self.assertTrue(extrude["params"]["through_all"])
        self.assertEqual(extrude["params"]["direction"], "negative")
        self.assertNotIn("distance", extrude["params"])

    @staticmethod
    def _slot_cases(width=6):
        return (
            (
                "sketch.slot.center_to_center",
                lambda: SlotCenterToCenter2D((1, 2), (21, 2), width),
            ),
            (
                "sketch.slot.overall",
                lambda: SlotOverall2D((-15, 4), (15, 4), width),
            ),
            (
                "sketch.slot.center_point",
                lambda: SlotCenterPoint2D((0, -6), (10, -6), width),
            ),
            (
                "sketch.slot.arc_three_point",
                lambda: SlotArcThreePoint2D(
                    (-15, 0), (0, 10), (15, 0), width
                ),
            ),
            (
                "sketch.slot.arc_center",
                lambda: SlotArcCenter2D(
                    (0, 0), (12, 0), width, sweep=120
                ),
            ),
        )

    def _compile_slot(self, command_name, factory, *, explicit_add):
        body = Box(80, 60, 5)
        with Sketch(on=body) as sketch:
            profile = factory()
            if explicit_add:
                sketch.add(profile)
                self.assertIsNone(
                    sketch._profiles[0][1],
                    (command_name, sketch._profiles),
                )
        commands = compile_model(
            body - sketch.extrude(Depth.THROUGH_ALL),
            "SlotAddRegression",
        )["commands"]
        return next(
            command
            for command in commands
            if command["command"] == command_name
        )

    def test_sketch_add_defaults_preserve_all_native_slot_coordinates(self):
        for command_name, factory in self._slot_cases():
            with self.subTest(command=command_name):
                automatic = self._compile_slot(
                    command_name,
                    factory,
                    explicit_add=False,
                )
                explicit = self._compile_slot(
                    command_name,
                    factory,
                    explicit_add=True,
                )
                self.assertEqual(explicit["params"], automatic["params"])

    def test_explicit_center_is_rejected_for_all_native_slots(self):
        for command_name, factory in self._slot_cases():
            with self.subTest(command=command_name):
                with self.assertRaisesRegex(
                    ValueError,
                    "coordinates; CENTER is not supported",
                ):
                    with Sketch(plane="XY") as sketch:
                        profile = factory()
                        sketch.add(profile, anchor=CENTER)

    def test_symbolic_width_lowers_on_all_native_slot_creators(self):
        width = Parameter("slot_width", 8)
        for command_name, factory in self._slot_cases(width):
            with self.subTest(command=command_name):
                command = self._compile_slot(
                    command_name,
                    factory,
                    explicit_add=False,
                )
                self.assertEqual(command["params"]["width"], "slot_width")

    def test_symbolic_width_still_validates_current_value(self):
        with self.assertRaisesRegex(ValueError, "positive finite"):
            SlotCenterToCenter2D(
                (0, 0),
                (20, 0),
                Parameter("slot_width", 0),
            )

    def test_arc_center_requires_one_end_definition(self):
        from scpf import SlotArcCenter2D
        with self.assertRaisesRegex(ValueError, "exactly one"):
            SlotArcCenter2D((0, 0), (10, 0), 4)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            SlotArcCenter2D((0, 0), (10, 0), 4, end=(0, 10), sweep=90)


if __name__ == "__main__":
    unittest.main()
