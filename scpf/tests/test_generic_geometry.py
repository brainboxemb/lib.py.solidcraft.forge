"""Standalone SCPF API geometry tests independent of real CAD projects."""
import unittest

from scpf import Sketch

class GenericGeometryAPI(unittest.TestCase):
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

    def test_fillet_and_chamfer_accept_the_same_box_edge_selectors(self):
        from scpf import FRONT, LEFT
        from scpf.core import Box, Edges

        selectors = (
            Edges.VERTICAL,
            FRONT + LEFT,
            [(-40, -25, 0)],
        )
        for operation in ("fillet", "chamfer"):
            method = getattr(Box(80, 50, 8), operation)
            self.assertIs(method(2).data[2], Edges.VERTICAL)
            for edges in selectors:
                with self.subTest(operation=operation, edges=edges):
                    result = method(2, edges=edges)
                    self.assertEqual(result.kind, operation)

            with self.assertRaises(ValueError):
                method(2, edges=FRONT)
            with self.assertRaises(ValueError):
                method(2, edges="vertical")
            with self.assertRaises(ValueError):
                method(2, edges=[(0, 0)])

    def test_fillet_and_chamfer_lower_box_edge_selectors_the_same(self):
        from scpf import FRONT, LEFT
        from scpf.core import Box, Edges
        from scpf.features import compile_features

        cases = (
            (
                Edges.VERTICAL,
                [[-40.0, -25.0, 0.0], [40.0, -25.0, 0.0],
                 [40.0, 25.0, 0.0], [-40.0, 25.0, 0.0]],
            ),
            (FRONT + LEFT, [[-40.0, -25.0, 0.0]]),
            ([(-40, -25, 0)], [[-40.0, -25.0, 0.0]]),
        )
        for edges, expected in cases:
            for operation in ("fillet", "chamfer"):
                with self.subTest(operation=operation, edges=edges):
                    shape = getattr(Box(80, 50, 8), operation)(2, edges=edges)
                    command = next(
                        row for row in compile_features(shape, "Body")
                        if row["command"] == f"solid.{operation}"
                    )
                    self.assertEqual(command["params"]["edges"], expected)

    def test_fillet_and_chamfer_share_profile_edge_resolution(self):
        from scpf.core import Edges, Polygon2D
        from scpf.features import compile_features

        with Sketch(plane="XZ") as sketch:
            Polygon2D([
                ("start", (0, 0)),
                ("tip", (10, 0)),
                ("far", (10, 8)),
                ("end", (0, 8)),
            ], plane="XZ", world=True)
        body = sketch.extrude(8, sym=True)

        for selection in (
            Edges.from_profile("start"),
            Edges.from_vertices("tip", "end"),
        ):
            picks = {}
            for operation in ("fillet", "chamfer"):
                with self.subTest(operation=operation, selection=selection):
                    shape = getattr(body, operation)(0.5, edges=selection)
                    command = next(
                        row for row in compile_features(shape, "Plate")
                        if row["command"] == f"solid.{operation}"
                    )
                    picks[operation] = command["params"]["edges"]
            self.assertEqual(picks["fillet"], picks["chamfer"])

    def test_missing_profile_edge_name_is_rejected(self):
        from scpf.core import Polygon2D, Edges
        from scpf.features import compile_features
        from scpf.compiler import ModelError

        with Sketch(plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (10, 0), (10, 10), (0, 10)],
                plane="XZ",
                ids=["bottom", "right", "top", "left"],
            )
        shape = sketch.extrude(10, sym=True)
        shape = shape.chamfer(1, edges=Edges.from_profile("o_*"))
        with self.assertRaisesRegex(ModelError, "no polygon segment or vertex matches"):
            compile_features(shape, "Square")

    def test_named_profile_selection_requires_segment_ids(self):
        from scpf.core import Polygon2D, Edges
        from scpf.features import compile_features
        from scpf.compiler import ModelError

        with Sketch(plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (10, 0), (10, 10), (0, 10)],
                plane="XZ",
            )
        shape = sketch.extrude(10, sym=True)
        shape = shape.chamfer(1, edges=Edges.from_profile("o_*"))
        with self.assertRaisesRegex(ModelError, "must define ids"):
            compile_features(shape, "Square")

    def test_sweep_edge_selection_uses_named_vertices(self):
        from scpf.core import Polygon2D, Edges
        from scpf.features import compile_features

        with Sketch(plane="XZ") as sketch:
            Polygon2D([
                ("start", (0, 0)), ("tip", (10, 0)),
                ("far", (10, 8)), ("end", (0, 8)),
            ], plane="XZ", world=True)
        shape = sketch.extrude(8, sym=True)
        shape = shape.chamfer(0.5, edges=Edges.from_vertices("tip", "end"))
        chamfer = next(
            c for c in compile_features(shape, "Plate")
            if c["command"] == "solid.chamfer"
        )
        self.assertEqual(chamfer["params"]["edges"], [[10, 0, 0], [0, 0, 8]])

    def test_copy_creates_a_second_occurrence_of_one_definition(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance, Placement

        original = ModelInstance(ModelDefinition("Panel", (), Box(20, 10, 2)))
        duplicate = original.copy(placement=Placement(x=24))
        self.assertIsNot(original, duplicate)
        self.assertIs(original.definition, duplicate.definition)
        self.assertEqual(original.placement.position, (0, 0, 0))
        self.assertEqual(duplicate.placement.position, (24, 0, 0))
        self.assertIsNone(duplicate.attachment)

    def test_taper_rejects_invalid_dimensions(self):
        from scpf.core import Box
        for kwargs in (
            {"from_z": 0, "inset": 1.25},
            {"from_z": 20, "inset": 1.25},
            {"from_z": 2, "inset": 100},
            {"from_z": 2, "inset": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Box(159.70, 319.71, 14.50).taper(**kwargs)


if __name__ == "__main__":
    unittest.main()
