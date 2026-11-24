"""Sketch contract tests."""
from pathlib import Path
import unittest

from scpf import (
    Anchor,
    Box,
    CENTER,
    Rectangle2D,
    Circle2D,
    Polygon2D,
    Depth,
    Edges,
    Sketch,
    Parameter,
)
from scpf.compiler import ModelError, compile_model
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[2]


class SketchAttachmentTests(unittest.TestCase):
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

    def test_attached_polygon_lowers_closed_native_line_and_cut(self):
        base = Box(80, 60, 5, anchor=Anchor.BOTTOM)
        with Sketch(name="Polygon cut", on=base, parent=Anchor.TOP) as sketch:
            Polygon2D([
                (-10, -8),
                (10, -8),
                (10, 8),
                (-10, 8),
            ])

        commands = compile_model(
            base - sketch.extrude(Depth.THROUGH_ALL),
            "PolygonCut",
        )["commands"]

        polygon = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.line"
        )
        self.assertTrue(polygon["closed"])
        self.assertEqual(
            polygon["points"],
            [[-10, -8], [10, -8], [10, 8], [-10, 8]],
        )
        self.assertEqual(len(polygon["ids"]), 4)

        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(extrude["operation"], "cut")
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")

    def test_focused_attached_through_all_example_still_compiles(self):
        document = run_script(
            ROOT / "examples/attached-through-all/scpf/model.py"
        )
        polygon = next(
            row["params"]
            for row in document["commands"]
            if row["command"] == "sketch.line"
        )
        self.assertTrue(polygon["closed"])
        self.assertEqual(len(polygon["points"]), 4)

        extrude = next(
            row["params"]
            for row in document["commands"]
            if row["command"] == "solid.extrude"
        )
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")
        self.assertEqual(extrude["operation"], "cut")

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

    def test_rotated_standalone_polygon_cutter_uses_world_sketch_frame(self):
        base = Box(60, 60, 20)
        with Sketch(
            name="Wedge",
            plane="XY",
            origin=(10, 5, 3),
            rotation=(90, 0, 45),
        ) as wedge:
            Polygon2D([(0, 0), (12, 0), (0, 6)])

        commands = compile_model(
            base - wedge.extrude(8),
            "RotatedCut",
        )["commands"]

        create = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
            and row["params"]["name"] == "Wedge"
        )
        self.assertEqual(create["plane"]["origin"], [10, 5, 3])
        for actual, expected in zip(
            create["plane"]["x_dir"],
            (2 ** -0.5, 2 ** -0.5, 0.0),
        ):
            self.assertAlmostEqual(actual, expected, places=9)
        for actual, expected in zip(
            create["plane"]["y_dir"],
            (0.0, 0.0, 1.0),
        ):
            self.assertAlmostEqual(actual, expected, places=9)

        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(extrude["operation"], "cut")
        self.assertEqual(extrude["targets"], ["RotatedCut"])

    def test_rotated_sketch_supports_second_reference_orientation(self):
        with Sketch(
            name="Second",
            plane="XY",
            rotation=(0, 45, 90),
        ) as sketch:
            Polygon2D([(0, 0), (8, 0), (0, 4)])

        commands = compile_model(sketch.extrude(5), "Second")["commands"]
        create = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
        )
        expected_x = (0.0, 2 ** -0.5, -(2 ** -0.5))
        expected_y = (-1.0, 0.0, 0.0)
        for actual, expected in zip(create["plane"]["x_dir"], expected_x):
            self.assertAlmostEqual(actual, expected, places=9)
        for actual, expected in zip(create["plane"]["y_dir"], expected_y):
            self.assertAlmostEqual(actual, expected, places=9)

    def test_sketch_rotation_requires_fixed_three_axis_degrees(self):
        for rotation in ((0, 45), (0, float("inf"), 0), ("90", 0, 0)):
            with self.subTest(rotation=rotation):
                with self.assertRaises(ValueError):
                    Sketch(plane="XY", rotation=rotation)

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
