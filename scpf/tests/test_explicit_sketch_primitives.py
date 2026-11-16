"""Regression contract: native primitives and explicit standalone sketches."""
import unittest

from scpf import (
    Anchor,
    Box,
    CENTER,
    Rectangle2D,
    Circle2D,
    Sketch,
    Parameter,
)
from scpf.compiler import compile_model


class NativePrimitiveTests(unittest.TestCase):
    def test_box_requires_no_implicit_sketch(self):
        commands = compile_model(
            Box(Parameter("length", 40), Parameter("width", 30),
                Parameter("height", 10)), "BoxModel"
        )["commands"]
        self.assertEqual(
            [c["command"] for c in commands],
            ["parameters.add", "parameters.add", "parameters.add", "solid.box"],
        )
        box = commands[-1]["params"]
        self.assertEqual(box["body_name"], "BoxModel")
        self.assertEqual(box["length"], "length")
        self.assertEqual(box["width"], "width")
        self.assertEqual(box["height"], "height")
        self.assertEqual(box["center"], [0, 0, 0])
        self.assertNotIn("corner", box)

    def test_2d_profile_has_no_direct_extrude_api(self):
        profile = Rectangle2D(40, 30)
        self.assertFalse(hasattr(profile, "extrude"))

    def test_rectangle_in_with_sketch_is_explicit(self):
        with Sketch(plane="XY") as sketch:
            Rectangle2D(40, 30)
        commands = compile_model(sketch.extrude(10), "Plate")["commands"]
        self.assertEqual(
            [c["command"] for c in commands],
            ["sketch.create", "sketch.rectangle.two_point",
             "sketch.finish", "solid.extrude"],
        )
        self.assertEqual(commands[1]["params"]["p0"], [-20, -15])
        self.assertEqual(commands[1]["params"]["p1"], [20, 15])
        self.assertEqual(commands[-1]["params"]["body_name"], "Plate")

    def test_center_is_public_short_form_for_anchor_center(self):
        self.assertIs(CENTER, Anchor.CENTER)

    def test_rectangle_center_then_deliberate_offset(self):
        with Sketch(plane="XY") as sketch:
            sketch.add(
                Rectangle2D(40, 30),
                offset=(5, -2),
            )
        commands = compile_model(sketch.extrude(10), "OffsetPlate")["commands"]
        rectangle = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.rectangle.two_point"
        )
        self.assertEqual(rectangle["p0"], [-15, -17])
        self.assertEqual(rectangle["p1"], [25, 13])

    def test_centered_rectangle_keeps_symbolic_dimensions(self):
        width = Parameter("width", 40)
        depth = Parameter("depth", 30)
        with Sketch(plane="XY") as sketch:
            sketch.add(Rectangle2D(width, depth))
        commands = compile_model(sketch.extrude(10), "SymbolicPlate")["commands"]
        rectangle = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.rectangle.two_point"
        )
        self.assertIn("width", rectangle["p0"][0])
        self.assertIn("width", rectangle["p1"][0])
        self.assertIn("depth", rectangle["p0"][1])
        self.assertIn("depth", rectangle["p1"][1])

    def test_polygon_auto_capture_keeps_authored_coordinates(self):
        from scpf import Polygon2D

        with Sketch(plane="XY") as sketch:
            Polygon2D([(0, 0), (20, 0), (20, 10), (0, 10)])
        commands = compile_model(sketch.extrude(5), "PolygonPlate")["commands"]
        line = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.line"
        )
        self.assertEqual(
            line["points"],
            [[0, 0], [20, 0], [20, 10], [0, 10]],
        )

    def test_text_explicit_offset_keeps_native_insertion_coordinates(self):
        from scpf.core import Text2D

        base = Box(80, 60, 5)
        with Sketch(
            name="Label",
            on=base,
            plane="XY",
            origin=(0, 0, 5),
        ) as sketch:
            sketch.add(
                Text2D("Pi 4", height=6.0, font="DejaVu Sans Bold"),
                offset=(-9, 18),
            )
        commands = compile_model(
            base - sketch.extrude(0.6, direction="negative"),
            "LabelledBox",
        )["commands"]
        text = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.text"
        )
        self.assertEqual(text["at"], [-9, 18])
        self.assertEqual(text["text"], "Pi 4")

    def test_explicit_center_is_rejected_for_text(self):
        from scpf.core import Text2D

        with self.assertRaisesRegex(ValueError, "CENTER is not supported"):
            with Sketch(plane="XY") as sketch:
                sketch.add(
                    Text2D("Label"),
                    anchor=CENTER,
                )

    def test_polygon_explicit_add_without_anchor_keeps_authored_coordinates(self):
        from scpf import Polygon2D

        with Sketch(plane="XY") as sketch:
            sketch.add(
                Polygon2D(
                    [(0, 0), (20, 0), (20, 10), (0, 10)]
                )
            )
        commands = compile_model(sketch.extrude(5), "PolygonAdded")["commands"]
        line = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.line"
        )
        self.assertEqual(
            line["points"],
            [[0, 0], [20, 0], [20, 10], [0, 10]],
        )

    def test_explicit_center_is_rejected_for_coordinate_defined_polygon(self):
        from scpf import Polygon2D

        with self.assertRaisesRegex(ValueError, "CENTER is not supported"):
            with Sketch(plane="XY") as sketch:
                sketch.add(
                    Polygon2D(
                        [(0, 0), (20, 0), (20, 10), (0, 10)]
                    ),
                    anchor=CENTER,
                )

    def test_circle_in_with_sketch_negative_extrusion(self):
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)
        commands = compile_model(
            sketch.extrude(30, direction="negative"), "Cylinder"
        )["commands"]
        self.assertEqual(commands[1]["command"], "sketch.circle.center")
        self.assertEqual(commands[-1]["params"]["direction"], "negative")

    def test_existing_attached_sketch_still_works(self):
        base = Box(80, 60, 5)
        with Sketch(name="Pad", on=base) as sketch:
            sketch.add(Rectangle2D(40, 30))
        commands = compile_model(base + sketch.extrude(8), "Part")["commands"]
        self.assertEqual(commands[0]["command"], "solid.box")
        self.assertEqual(
            [c["command"] for c in commands].count("sketch.create"), 1
        )

    def test_empty_sketch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one profile"):
            with Sketch(plane="XY"):
                pass


if __name__ == "__main__":
    unittest.main()
