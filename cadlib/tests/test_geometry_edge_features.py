"""Fillet, chamfer, taper and edge-selection contracts."""
import unittest

from scpf import Sketch

class GeometryEdgeFeatureTests(unittest.TestCase):
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
