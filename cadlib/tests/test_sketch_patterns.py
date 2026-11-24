"""Q1/Q2 contract for associative sketch pattern and mirror operations."""

import unittest

from scpf import (
    Anchor,
    Axis,
    Box,
    Circle2D,
    Depth,
    Sketch,
    SlotCenterToCenter2D,
)
from scpf.compiler import compile_model
from scpf.core import Parameter


class SketchPatternMirrorTests(unittest.TestCase):
    def test_circle_rectangular_pattern_uses_bound_native_curves(self):
        board = Box(120, 90, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Dog holes", on=board, parent=Anchor.TOP) as sketch:
            seed = sketch.add(Circle2D(d=8), offset=(-30, -10))
            patterned = sketch.rectangular_pattern(
                seed,
                count=4,
                spacing=20,
                direction=Axis.X,
                count2=2,
                spacing2=20,
                direction2=Axis.Y,
            )
            sketch.mirror(patterned, axis=Axis.Y)

        document = compile_model(
            board - sketch.extrude(Depth.THROUGH_ALL),
            "PatternBoard",
        )
        self.assertEqual(document["format"], "scpf-replay")
        commands = document["commands"]

        circle = next(
            command for command in commands
            if command["command"] == "sketch.circle.center"
        )
        self.assertEqual(
            circle["bind"],
            {"$sketch_1_profile_1": "curves"},
        )

        pattern = next(
            command for command in commands
            if command["command"] == "sketch.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["entities"], "$sketch_1_profile_1")
        self.assertEqual(pattern["params"]["count"], 4)
        self.assertEqual(pattern["params"]["spacing"], 20)
        self.assertEqual(pattern["params"]["dir"], [1.0, 0.0])
        self.assertEqual(pattern["params"]["count2"], 2)
        self.assertEqual(pattern["params"]["spacing2"], 20)
        self.assertEqual(pattern["params"]["dir2"], [0.0, 1.0])
        self.assertEqual(
            pattern["bind"],
            {
                "$sketch_1_operation_1": {
                    "field": "curves",
                    "prepend": "$sketch_1_profile_1",
                }
            },
        )

        names = [command["command"] for command in commands]
        self.assertEqual(names.count("sketch.create"), 1)
        self.assertEqual(names.count("sketch.circle.center"), 1)
        self.assertEqual(names.count("sketch.pattern.rectangular"), 1)
        self.assertEqual(names.count("sketch.mirror"), 1)
        self.assertEqual(names.count("sketch.finish"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)

    def test_slot_pattern_and_mirrors_reuse_operation_results(self):
        board = Box(160, 120, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Clamp slots", on=board, parent=Anchor.TOP) as sketch:
            seed = SlotCenterToCenter2D((20, 20), (40, 40), 8)
            arm = sketch.rectangular_pattern(
                seed,
                count=2,
                spacing=50,
                direction=(1, 1),
            )
            mirrored_y = sketch.mirror(arm, axis=Axis.Y)
            sketch.mirror(arm, axis=Axis.X)
            sketch.mirror(mirrored_y, axis=Axis.X)

        commands = compile_model(
            board - sketch.extrude(Depth.THROUGH_ALL),
            "SlotBoard",
        )["commands"]

        slot = next(
            command for command in commands
            if command["command"] == "sketch.slot.center_to_center"
        )
        self.assertEqual(
            slot["bind"],
            {"$sketch_1_profile_1": "curves"},
        )

        pattern = next(
            command for command in commands
            if command["command"] == "sketch.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["entities"], "$sketch_1_profile_1")
        self.assertEqual(pattern["params"]["count"], 2)
        self.assertEqual(pattern["params"]["spacing"], 50)
        self.assertEqual(pattern["params"]["dir"], [1.0, 1.0])
        self.assertEqual(
            pattern["bind"],
            {
                "$sketch_1_operation_1": {
                    "field": "curves",
                    "prepend": "$sketch_1_profile_1",
                }
            },
        )

        mirrors = [
            command for command in commands
            if command["command"] == "sketch.mirror"
        ]
        self.assertEqual(len(mirrors), 3)
        self.assertEqual(
            mirrors[0]["params"],
            {"entities": "$sketch_1_operation_1", "line": "y"},
        )
        self.assertEqual(
            mirrors[1]["params"],
            {"entities": "$sketch_1_operation_1", "line": "x"},
        )
        self.assertEqual(
            mirrors[2]["params"],
            {"entities": "$sketch_1_operation_2", "line": "x"},
        )

        names = [command["command"] for command in commands]
        self.assertEqual(names.count("sketch.create"), 1)
        self.assertEqual(names.count("sketch.slot.center_to_center"), 1)
        self.assertEqual(names.count("sketch.pattern.rectangular"), 1)
        self.assertEqual(names.count("sketch.mirror"), 3)
        self.assertEqual(names.count("sketch.finish"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)

    def test_parametric_slot_pattern_keeps_profile_and_runtime_bindings(self):
        board = Box(140, 90, 5, anchor=Anchor.BOTTOM)
        start = Parameter("slot_start", 20)
        end = Parameter("slot_end", 40)
        y = Parameter("slot_y", 15)

        with Sketch(
            name="Parametric clamp slots",
            on=board,
            parent=Anchor.TOP,
        ) as sketch:
            seed = SlotCenterToCenter2D(
                (start, y),
                (end, y),
                8,
            )
            sketch.rectangular_pattern(
                seed,
                count=2,
                spacing=50,
                direction=Axis.X,
            )

        commands = compile_model(
            board - sketch.extrude(Depth.THROUGH_ALL),
            "ParametricSlotBoard",
        )["commands"]

        dimensioned = next(
            row for row in commands
            if row["command"] == "sketch.draw.dimensioned"
        )
        self.assertEqual(
            dimensioned["bind"]["$sketch_1_profile_1"],
            "curves",
        )
        self.assertIn(
            "centre_line",
            set(dimensioned["bind"].values()),
        )
        self.assertIn(
            "middle",
            set(dimensioned["bind"].values()),
        )

        pattern = next(
            row for row in commands
            if row["command"] == "sketch.pattern.rectangular"
        )
        self.assertEqual(
            pattern["params"]["entities"],
            "$sketch_1_profile_1",
        )

    def test_pattern_count_and_spacing_remain_native_parameters(self):
        board = Box(120, 90, 5, anchor=Anchor.BOTTOM)
        columns = Parameter("columns", 4)
        pitch = Parameter("pitch", 20)

        with Sketch(name="Parametric holes", on=board, parent=Anchor.TOP) as sketch:
            seed = sketch.add(Circle2D(d=8), offset=(-30, 0))
            sketch.rectangular_pattern(
                seed,
                count=columns,
                spacing=pitch,
                direction=Axis.X,
            )

        document = compile_model(
            board - sketch.extrude(Depth.THROUGH_ALL),
            "ParametricPatternBoard",
        )
        commands = document["commands"]
        pattern = next(
            command for command in commands
            if command["command"] == "sketch.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["count"], "columns")
        self.assertEqual(pattern["params"]["spacing"], "pitch")

        units = {
            command["params"]["name"]: command["params"]["unit"]
            for command in commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(units["columns"], "")
        self.assertEqual(units["pitch"], "mm")

    def test_pattern_can_feed_one_selective_profile_extrusion(self):
        board = Box(120, 80, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Selected holes", on=board, parent=Anchor.TOP) as sketch:
            seed = sketch.add(Circle2D(d=8), offset=(-30, 0))
            sketch.rectangular_pattern(
                seed,
                count=4,
                spacing=20,
                direction=Axis.X,
            )

        commands = compile_model(
            board - sketch.extrude(
                Depth.THROUGH_ALL,
                profiles=[(-30, 0), (-10, 0), (30, 0)],
                exact_regions=True,
            ),
            "SelectedPatternBoard",
        )["commands"]

        self.assertEqual(
            [row["command"] for row in commands].count(
                "sketch.pattern.rectangular"
            ),
            1,
        )
        self.assertEqual(
            [row["command"] for row in commands].count("sketch.circle.center"),
            1,
        )
        extrude = next(
            row["params"]
            for row in commands
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

    def test_pattern_source_must_belong_to_same_sketch(self):
        foreign = Circle2D(d=8)
        board = Box(80, 60, 5)

        with self.assertRaisesRegex(ValueError, "belong to this Sketch"):
            with Sketch(name="Pattern", on=board) as sketch:
                local = Circle2D(d=6)
                sketch.rectangular_pattern(
                    foreign,
                    count=2,
                    spacing=20,
                )
                self.assertIsNotNone(local)

    def test_standalone_pattern_is_rejected_at_compile_time(self):
        with Sketch(name="Standalone", plane="XY") as sketch:
            seed = Circle2D(d=8)
            sketch.rectangular_pattern(seed, count=2, spacing=20)

        with self.assertRaisesRegex(
            ValueError,
            "currently requires an attached Sketch",
        ):
            compile_model(sketch.extrude(5), "StandalonePattern")


if __name__ == "__main__":
    unittest.main()
