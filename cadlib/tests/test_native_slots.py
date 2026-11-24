"""Q1/Q2 tests for the five native SolidCraft Slot constructors."""
import unittest
from pathlib import Path

from scpf import (
    Box,
    CENTER,
    Depth,
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
        slot_commands = []
        for command in commands:
            if command["command"].startswith("sketch.slot."):
                slot_commands.append(command)
            elif (
                command["command"] == "sketch.draw.dimensioned"
                and command["params"]["command"].startswith("sketch.slot.")
            ):
                slot_commands.append({
                    "command": command["params"]["command"],
                    "params": command["params"]["params"],
                })
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
            all(
                command["params"]["width"] == "slot_width"
                for command in slot_commands
            )
        )
        self.assertEqual(slot_commands[-1]["params"]["sweep"], 120)

        # The parent Box dimensions are editable Parameters. Fixed Slot-local
        # coordinates must remain numeric instead of inheriting symbolic
        # width/depth expressions from the attached Sketch target.
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
    def _slot_cases():
        return (
            (
                "sketch.slot.center_to_center",
                lambda: SlotCenterToCenter2D((1, 2), (21, 2), 6),
            ),
            (
                "sketch.slot.overall",
                lambda: SlotOverall2D((-15, 4), (15, 4), 6),
            ),
            (
                "sketch.slot.center_point",
                lambda: SlotCenterPoint2D((0, -6), (10, -6), 6),
            ),
            (
                "sketch.slot.arc_three_point",
                lambda: SlotArcThreePoint2D(
                    (-15, 0), (0, 10), (15, 0), 6
                ),
            ),
            (
                "sketch.slot.arc_center",
                lambda: SlotArcCenter2D(
                    (0, 0), (12, 0), 6, sweep=120
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

    def test_symbolic_width_stays_native_for_all_slot_creators(self):
        from scpf import Parameter

        width = Parameter("slot_width", 8)
        cases = (
            (
                "sketch.slot.center_to_center",
                lambda: SlotCenterToCenter2D((0, 0), (20, 0), width),
            ),
            (
                "sketch.slot.overall",
                lambda: SlotOverall2D((-15, 0), (15, 0), width),
            ),
            (
                "sketch.slot.center_point",
                lambda: SlotCenterPoint2D((0, 0), (10, 0), width),
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

        for command_name, factory in cases:
            with self.subTest(command=command_name):
                slot = self._compile_slot(
                    command_name,
                    factory,
                    explicit_add=False,
                )
                self.assertEqual(slot["params"]["width"], "slot_width")
                body = Box(80, 60, 5)
                with Sketch(on=body) as sketch:
                    factory()
                commands = compile_model(
                    body - sketch.extrude(Depth.THROUGH_ALL),
                    "ParametricSlotWidth",
                )["commands"]
                parameter = next(
                    row["params"]
                    for row in commands
                    if row["command"] == "parameters.add"
                    and row["params"]["name"] == "slot_width"
                )
                self.assertEqual(float(parameter["expression"]), 8.0)
                self.assertEqual(parameter["unit"], "mm")

    def _compile_dimensioned_slot(self, factory):
        body = Box(100, 80, 5)
        with Sketch(name="Parametric slot", on=body) as sketch:
            factory()
        return compile_model(
            body - sketch.extrude(Depth.THROUGH_ALL),
            "ParametricSlot",
        )["commands"]

    def test_parametric_straight_slots_use_native_dimensioned_creation(self):
        from scpf import Parameter

        y = Parameter("slot_y", -12)
        width = Parameter("slot_width", 8)

        cases = (
            (
                "sketch.slot.center_to_center",
                lambda: SlotCenterToCenter2D(
                    (Parameter("c2c_start", -25), y),
                    (Parameter("c2c_end", 15), y),
                    width,
                ),
                ("p0", "p1"),
                ("c2c_start", "c2c_end"),
            ),
            (
                "sketch.slot.overall",
                lambda: SlotOverall2D(
                    (Parameter("overall_start", -20), y),
                    (Parameter("overall_end", 20), y),
                    width,
                ),
                ("p0", "p1"),
                ("overall_start", "overall_end"),
            ),
            (
                "sketch.slot.center_point",
                lambda: SlotCenterPoint2D(
                    (Parameter("slot_center", 5), y),
                    (Parameter("slot_end", 25), y),
                    width,
                ),
                ("center", "end"),
                ("slot_center", "slot_end"),
            ),
        )

        for command_name, factory, point_keys, length_names in cases:
            with self.subTest(command=command_name):
                commands = self._compile_dimensioned_slot(factory)
                dimensioned = next(
                    row
                    for row in commands
                    if row["command"] == "sketch.draw.dimensioned"
                )
                self.assertEqual(
                    dimensioned["params"]["command"],
                    command_name,
                )
                params = dimensioned["params"]["params"]
                for key in point_keys:
                    self.assertTrue(
                        all(isinstance(value, (int, float))
                            for value in params[key]),
                        (command_name, key, params[key]),
                    )
                self.assertEqual(params["width"], "slot_width")

                length = str(
                    dimensioned["params"]["dimensions"]["length"]
                )
                for name in length_names:
                    self.assertIn(name, length)
                if command_name == "sketch.slot.center_point":
                    self.assertIn("* 2", length)

                bind = dimensioned["bind"]
                centre_line = next(
                    key for key, value in bind.items()
                    if value == "centre_line"
                )
                middle = next(
                    key for key, value in bind.items()
                    if value == "middle"
                )

                orientation = next(
                    row["params"]
                    for row in commands
                    if (
                        row["command"]
                        == "sketch.constraint.horizontal_vertical"
                        and row["params"]["line"] == centre_line
                    )
                )
                self.assertEqual(orientation["mode"], "horizontal")

                position = [
                    row["params"]
                    for row in commands
                    if (
                        row["command"] == "sketch.dimension"
                        and row["params"]["entities"] == ["origin", middle]
                    )
                ]
                self.assertEqual(
                    {row["type"] for row in position},
                    {"horizontal", "vertical"},
                )
                vertical = next(
                    row for row in position
                    if row["type"] == "vertical"
                )
                self.assertIn("slot_y", str(vertical["value"]))
                self.assertIn("abs(", str(vertical["value"]))
                horizontal = next(
                    row for row in position
                    if row["type"] == "horizontal"
                )
                if command_name == "sketch.slot.center_point":
                    self.assertIn(
                        "slot_center",
                        str(horizontal["value"]),
                    )
                else:
                    for name in length_names:
                        self.assertIn(name, str(horizontal["value"]))

                names = {
                    row["params"]["name"]
                    for row in commands
                    if row["command"] == "parameters.add"
                }
                self.assertIn("slot_y", names)
                self.assertIn("slot_width", names)
                self.assertTrue(set(length_names).issubset(names))

    def test_vertical_parametric_straight_slot_keeps_native_axis(self):
        from scpf import Parameter

        x = Parameter("slot_x", -9)
        start = Parameter("slot_start_y", -20)
        end = Parameter("slot_end_y", 20)
        commands = self._compile_dimensioned_slot(
            lambda: SlotCenterToCenter2D(
                (x, start),
                (x, end),
                Parameter("slot_width", 6),
            )
        )

        dimensioned = next(
            row for row in commands
            if row["command"] == "sketch.draw.dimensioned"
        )
        centre_line = next(
            key for key, value in dimensioned["bind"].items()
            if value == "centre_line"
        )
        orientation = next(
            row["params"]
            for row in commands
            if (
                row["command"] == "sketch.constraint.horizontal_vertical"
                and row["params"]["line"] == centre_line
            )
        )
        self.assertEqual(orientation["mode"], "vertical")

        middle = next(
            key for key, value in dimensioned["bind"].items()
            if value == "middle"
        )
        horizontal = next(
            row["params"]
            for row in commands
            if (
                row["command"] == "sketch.dimension"
                and row["params"]["entities"] == ["origin", middle]
                and row["params"]["type"] == "horizontal"
            )
        )
        self.assertIn("slot_x", str(horizontal["value"]))
        self.assertIn("abs(", str(horizontal["value"]))

    def test_parametric_straight_slot_requires_matching_perpendicular_intent(self):
        from scpf import Parameter
        from scpf.compiler import ModelError

        y0 = Parameter("slot_y_a", 0)
        y1 = Parameter("slot_y_b", 0)
        with self.assertRaisesRegex(
            ModelError,
            "same y-coordinate intent",
        ):
            self._compile_dimensioned_slot(
                lambda: SlotCenterToCenter2D(
                    (Parameter("slot_start", -20), y0),
                    (Parameter("slot_end", 20), y1),
                    6,
                )
            )

    def test_parametric_diagonal_straight_slot_is_rejected(self):
        from scpf import Parameter
        from scpf.compiler import ModelError

        with self.assertRaisesRegex(
            ModelError,
            "horizontal or vertical axis",
        ):
            self._compile_dimensioned_slot(
                lambda: SlotCenterToCenter2D(
                    (
                        Parameter("slot_x0", 0),
                        Parameter("slot_y0", 0),
                    ),
                    (
                        Parameter("slot_x1", 20),
                        Parameter("slot_y1", 10),
                    ),
                    6,
                )
            )

    def test_fixed_diagonal_straight_slot_stays_direct_native(self):
        commands = self._compile_dimensioned_slot(
            lambda: SlotCenterToCenter2D((0, 0), (20, 10), 6)
        )
        self.assertEqual(
            [row["command"] for row in commands].count(
                "sketch.slot.center_to_center"
            ),
            1,
        )
        self.assertNotIn(
            "sketch.draw.dimensioned",
            [row["command"] for row in commands],
        )

    def test_arc_slot_authored_points_remain_fixed(self):
        from scpf import Parameter

        with self.assertRaisesRegex(TypeError, "fixed numeric coordinates"):
            SlotArcThreePoint2D(
                (Parameter("arc_x", -10), 0),
                (0, 10),
                (10, 0),
                6,
            )

    def test_symbolic_slot_width_still_requires_positive_current_value(self):
        from scpf import Parameter

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
