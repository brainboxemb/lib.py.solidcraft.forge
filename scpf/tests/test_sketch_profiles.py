"""Polygon and parameterised Sketch profile contracts."""
import unittest

from scpf import Sketch

class SketchProfileTests(unittest.TestCase):
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
