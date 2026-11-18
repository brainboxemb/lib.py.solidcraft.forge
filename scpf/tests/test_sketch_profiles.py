"""Sketch contract tests."""
import unittest

from scpf import (
    Anchor,
    Box,
    CENTER,
    Rectangle2D,
    Circle2D,
    Depth,
    Edges,
    Sketch,
    Parameter,
)
from scpf.compiler import ModelError, compile_model

class SketchProfileTests(unittest.TestCase):
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
            base - sketch.extrude(-0.6),
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
        commands = compile_model(sketch.extrude(-30), "Cylinder")["commands"]
        self.assertEqual(commands[1]["command"], "sketch.circle.center")
        self.assertEqual(commands[-1]["params"]["distance"], 30)
        self.assertEqual(commands[-1]["params"]["direction"], "negative")

    def test_named_polygon_vertices_generate_sketch_ids(self):
        from scpf.core import Polygon2D
        profile = Polygon2D([
            ("bottom", (0, 0)), ("right", (10, 0)),
            ("top", (10, 8)), ("left", (0, 8)),
        ], plane="XZ", world=True)
        points, plane, ids = profile.data
        self.assertEqual(plane, "XZ")
        self.assertEqual(points, ((0, 0), (10, 0), (10, -8), (0, -8)))
        self.assertEqual(ids, ("bottom", "right", "top", "left"))

        with self.assertRaisesRegex(ValueError, "all polygon vertices"):
            Polygon2D([("a", (0, 0)), (10, 0), (10, 10)])
        with self.assertRaisesRegex(ValueError, "cannot also specify ids"):
            Polygon2D([("a", (0, 0)), ("b", (10, 0)), ("c", (0, 10))],
                      ids=["a", "b", "c"])

    def test_polygon_segment_ids_are_checked(self):
        from scpf.core import Polygon2D
        points = [(0, 0), (10, 0), (10, 10)]
        for tags in (["a", "b"], ["a", "a", "c"], ["a", "bad id", "c"]):
            with self.subTest(tags=tags), self.assertRaises(ValueError):
                Polygon2D(points, ids=tags)

    def test_unpositioned_polygon_keeps_parameters_for_all_extrusion_directions(self):
        from scpf.core import Parameter, Polygon2D
        from scpf.features import compile_features

        width = Parameter("opening_width", 844.0)
        trim = Parameter("glazing_wood_width", 12.0)

        for distance in (12, -12):
            with self.subTest(distance=distance):
                with Sketch(plane="XZ") as sketch:
                    Polygon2D([
                        (-width / 2, 0),
                        (width / 2, 0),
                        (width / 2 - trim, trim),
                        (-width / 2 + trim, trim),
                    ], plane="XZ", world=True)
                shape = sketch.extrude(distance)
                commands = compile_features(shape, "Strip")
                line = next(
                    command["params"]
                    for command in commands
                    if command["command"] == "sketch.line"
                )
                points = str(line["points"])
                self.assertIn("opening_width", points)
                self.assertIn("glazing_wood_width", points)

    def test_positioned_xz_polygon_keeps_parameterized_y_plane(self):
        from scpf.core import Edges, Parameter, Polygon2D
        from scpf.features import compile_features

        rear = Parameter("cabinet_depth", 100.0)
        depth = Parameter("panel_wood_thickness", 9.0)
        with Sketch(plane="XZ", offset=rear) as sketch:
            Polygon2D([
                ("lower_left", (-10, 0)),
                ("lower_right", (10, 0)),
                ("upper_right", (10, 20)),
                ("upper_left", (-10, 20)),
            ], plane="XZ", world=True)
        shape = sketch.extrude(depth).fillet(
            1,
            edges=Edges.from_vertices("lower_left"),
        )

        commands = compile_features(shape, "BackBoard")
        sketch = next(
            item["params"]
            for item in commands
            if item["command"] == "sketch.create"
        )
        extrusion = next(
            item["params"]
            for item in commands
            if item["command"] == "solid.extrude"
        )
        fillet = next(
            item["params"]
            for item in commands
            if item["command"] == "solid.fillet"
        )

        self.assertEqual(sketch["plane"], "XZ")
        self.assertEqual(sketch["offset"], "cabinet_depth")
        self.assertEqual(extrusion["distance"], "panel_wood_thickness")
        self.assertEqual(extrusion["direction"], "positive")
        self.assertEqual(fillet["edges"], [[-10.0, 104.5, 0.0]])
