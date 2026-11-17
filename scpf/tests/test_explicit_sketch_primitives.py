"""Regression contract: native primitives and explicit standalone sketches."""
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

    def test_sketch_extrude_signed_distance_and_sym(self):
        height = Parameter("height", 30)
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)

        positive = compile_model(sketch.extrude(height), "Positive")["commands"][-1]["params"]
        negative = compile_model(sketch.extrude(-height), "Negative")["commands"][-1]["params"]
        symmetric = compile_model(
            sketch.extrude(height, sym=True), "Symmetric"
        )["commands"][-1]["params"]

        self.assertEqual(positive["distance"], "height")
        self.assertEqual(positive["direction"], "positive")
        self.assertEqual(negative["distance"], "height")
        self.assertEqual(negative["direction"], "negative")
        self.assertEqual(symmetric["distance"], "height")
        self.assertEqual(symmetric["direction"], "symmetric")

        with self.assertRaisesRegex(ValueError, "non-zero"):
            sketch.extrude(0)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            sketch.extrude(-10, sym=True)
        with self.assertRaisesRegex(TypeError, "True or False"):
            sketch.extrude(10, sym="yes")

    def test_sketch_extrude_profile_points_lower_for_standalone_and_attached(self):
        with Sketch(name="Standalone", plane="XY") as standalone:
            Circle2D(d=20)
        standalone_extrude = compile_model(
            standalone.extrude(
                10,
                profiles=[(0, 0)],
                exact_regions=True,
            ),
            "StandaloneSelected",
        )["commands"][-1]["params"]
        self.assertEqual(
            standalone_extrude["profiles"],
            [{"point": [0.0, 0.0]}],
        )
        self.assertTrue(standalone_extrude["exact_regions"])

        base = Box(80, 60, 5, anchor=Anchor.BOTTOM)
        with Sketch(name="Attached", on=base, parent=Anchor.TOP) as attached:
            attached.add(Circle2D(d=10), offset=(-15, 0))
            attached.add(Circle2D(d=10), offset=(15, 0))
        commands = compile_model(
            base - attached.extrude(
                Depth.THROUGH_ALL,
                profiles=[(-15, 0)],
                exact_regions=True,
            ),
            "AttachedSelected",
        )["commands"]
        attached_extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(
            attached_extrude["profiles"],
            [{"point": [-15.0, 0.0]}],
        )
        self.assertTrue(attached_extrude["exact_regions"])

    def test_sketch_extrude_default_keeps_all_profiles(self):
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)
        extrude = compile_model(
            sketch.extrude(10),
            "AllProfiles",
        )["commands"][-1]["params"]
        self.assertNotIn("profiles", extrude)
        self.assertNotIn("exact_regions", extrude)

    def test_sketch_extrude_profile_selection_validates_points(self):
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)

        invalid_profiles = (
            [],
            [(0,)],
            [(0, 0, 0)],
            [("x", 0)],
            [(True, 0)],
            [(float("nan"), 0)],
            [(Parameter("pick", 0), 0)],
        )
        for profiles in invalid_profiles:
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):
                sketch.extrude(10, profiles=profiles)

        with self.assertRaisesRegex(TypeError, "exact_regions"):
            sketch.extrude(10, profiles=[(0, 0)], exact_regions="yes")
        with self.assertRaisesRegex(ValueError, "requires profiles"):
            sketch.extrude(10, exact_regions=True)

    def test_attached_through_all_uses_support_face_direction(self):
        for parent, expected_direction in (
            (Anchor.TOP, "negative"),
            (Anchor.BOTTOM, "positive"),
        ):
            with self.subTest(parent=parent):
                base = Box(80, 60, 5, anchor=Anchor.BOTTOM)
                with Sketch(name="Cut", on=base, parent=parent) as sketch:
                    Circle2D(d=10)

                commands = compile_model(
                    base - sketch.extrude(Depth.THROUGH_ALL),
                    "Part",
                )["commands"]
                extrude = next(
                    row["params"]
                    for row in commands
                    if row["command"] == "solid.extrude"
                )

                self.assertTrue(extrude["through_all"])
                self.assertEqual(
                    extrude["direction"],
                    expected_direction,
                )
                self.assertEqual(extrude["operation"], "cut")
                self.assertNotIn("distance", extrude)

    def test_existing_attached_sketch_still_works(self):
        base = Box(80, 60, 5)
        with Sketch(name="Pad", on=base) as sketch:
            sketch.add(Rectangle2D(40, 30))
        commands = compile_model(base + sketch.extrude(8), "Part")["commands"]
        self.assertEqual(commands[0]["command"], "solid.box")
        self.assertEqual(
            [c["command"] for c in commands].count("sketch.create"), 1
        )

    def test_top_attached_sketch_uses_same_face_query_after_edge_features(self):
        for operation in ("chamfer", "fillet"):
            with self.subTest(operation=operation):
                base = Box(100, 70, 10, anchor=Anchor.BOTTOM)
                featured = getattr(base, operation)(
                    2,
                    edges=Edges.VERTICAL,
                )
                with Sketch(
                    name="Top cut",
                    on=featured,
                    parent=Anchor.TOP,
                ) as sketch:
                    Circle2D(d=12)

                commands = compile_model(
                    featured - sketch.extrude(Depth.THROUGH_ALL),
                    f"{operation.title()}Plate",
                )["commands"]

                feature_index = next(
                    index
                    for index, row in enumerate(commands)
                    if row["command"] == f"solid.{operation}"
                )
                face_index = next(
                    index
                    for index, row in enumerate(commands)
                    if row["command"] == "model.faces"
                )
                self.assertLess(feature_index, face_index)

                face_query = commands[face_index]
                self.assertEqual(
                    face_query["params"],
                    {"body": f"{operation.title()}Plate"},
                )
                for spec in face_query["bind"].values():
                    self.assertEqual(
                        spec["where"],
                        {"plane_normal": [0, 0, 1]},
                    )
                    self.assertEqual(spec["max"], "area")

                top_sketch = commands[face_index + 1]
                self.assertEqual(top_sketch["command"], "sketch.create")
                self.assertEqual(
                    top_sketch["params"]["plane"]["body"],
                    f"{operation.title()}Plate",
                )

    def test_top_attached_sketch_supports_circular_extrusion_body(self):
        with Sketch(name="Disc", plane="XY") as disc:
            Circle2D(d=100)
        body = disc.extrude(10)

        with Sketch(name="Hub", on=body, parent=Anchor.TOP) as hub:
            Circle2D(d=44)

        commands = compile_model(
            body + hub.extrude(16),
            "Flange",
        )["commands"]

        face_query = next(
            row for row in commands
            if row["command"] == "model.faces"
        )
        self.assertEqual(face_query["params"], {"body": "Flange"})
        for spec in face_query["bind"].values():
            self.assertEqual(
                spec["where"],
                {"plane_normal": [0, 0, 1]},
            )
            self.assertEqual(spec["max"], "area")

        sketch = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
            and row["params"]["name"] == "Hub"
        )
        self.assertEqual(sketch["plane"]["body"], "Flange")

    def test_explicit_plane_origin_sketch_supports_circular_body(self):
        with Sketch(name="Disc", plane="XY") as disc:
            Circle2D(d=100)
        body = disc.extrude(10)

        with Sketch(
            name="Bore",
            on=body,
            plane="XY",
            origin=(0, 0, 0),
        ) as bore:
            Circle2D(d=24)

        commands = compile_model(
            body - bore.extrude(10),
            "Flange",
        )["commands"]

        sketch = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
            and row["params"]["name"] == "Bore"
        )
        self.assertEqual(
            sketch["plane"],
            {
                "origin": [0, 0, 0],
                "x_dir": [1, 0, 0],
                "y_dir": [0, 1, 0],
            },
        )
        self.assertNotIn(
            "model.faces",
            [row["command"] for row in commands],
        )

    def test_bottom_attached_sketch_keeps_rectangular_body_requirement(self):
        with Sketch(name="Disc", plane="XY") as disc:
            Circle2D(d=100)
        body = disc.extrude(10)

        with Sketch(
            name="Bottom",
            on=body,
            parent=Anchor.BOTTOM,
        ) as bottom:
            Circle2D(d=10)

        with self.assertRaisesRegex(
            ModelError,
            "BOTTOM/CENTER attached Sketch currently requires",
        ):
            compile_model(
                body - bottom.extrude(5),
                "DiscBody",
            )

    def test_empty_sketch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one profile"):
            with Sketch(plane="XY"):
                pass


if __name__ == "__main__":
    unittest.main()
