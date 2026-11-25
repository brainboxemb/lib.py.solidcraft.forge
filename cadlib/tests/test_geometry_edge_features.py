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

    def test_face_boundary_selector_compiles_box_topology_to_native_refs(self):
        from scpf.core import Box, Edges, Faces
        from scpf.features import compile_features

        shape = Box(80, 50, 8).chamfer(
            2, edges=Edges.from_faces(Faces.TOP)
        )
        commands = compile_features(shape, "Body")
        face_query = next(
            row for row in commands if row["command"] == "model.faces"
        )
        edge_query = next(
            row for row in commands if row["command"] == "model.edges"
        )
        chamfer = next(
            row for row in commands if row["command"] == "solid.chamfer"
        )
        self.assertEqual(
            face_query["bind"]["$topology_face_1"]["where"]["plane_normal"],
            [0, 0, 1],
        )
        self.assertEqual(
            edge_query["bind"]["$topology_edges_1"]["boundary_of"],
            "$topology_face_1",
        )
        self.assertEqual(chamfer["params"]["edges"], "$topology_edges_1")

    def test_face_boundary_selector_compiles_xz_broad_faces_as_front_back(self):
        from scpf.core import Edges, Faces, Polygon2D
        from scpf.features import compile_features

        with Sketch(plane="XZ") as sketch:
            Polygon2D(
                [(-20, 0), (20, 0), (20, 30), (-20, 30)],
                plane="XZ",
                world=True,
            )
        body = sketch.extrude(15, sym=True)
        shape = body.chamfer(
            1.5,
            edges=Edges.from_faces(Faces.FRONT, Faces.BACK),
        )
        commands = compile_features(shape, "Hook")
        face_queries = [
            row for row in commands if row["command"] == "model.faces"
        ]
        normals = []
        for index, row in enumerate(face_queries, start=1):
            normals.append(
                row["bind"][f"$topology_face_{index}"]["where"]["plane_normal"]
            )
        self.assertEqual(normals, [[0, -1, 0], [0, 1, 0]])
        edge_queries = [
            row for row in commands if row["command"] == "model.edges"
        ]
        self.assertEqual(
            edge_queries[1]["bind"]["$topology_edges_2"]["prepend"],
            "$topology_edges_1",
        )
        chamfer = next(
            row for row in commands if row["command"] == "solid.chamfer"
        )
        self.assertEqual(chamfer["params"]["edges"], "$topology_edges_2")

    def test_shell_uses_the_same_native_faces_vocabulary(self):
        from scpf.core import Box, Faces
        from scpf.features import compile_features

        commands = compile_features(
            Box(40, 30, 20).shell(2, open=Faces.LEFT),
            "Case",
        )
        face_query = next(
            row for row in commands if row["command"] == "model.faces"
        )
        shell = next(
            row for row in commands if row["command"] == "solid.shell"
        )
        self.assertEqual(
            face_query["bind"]["$topology_face_name_1"]["where"]["plane_normal"],
            [-1, 0, 0],
        )
        self.assertEqual(shell["params"]["faces"], ["$topology_face_name_1"])

    def test_on_accepts_shared_faces_before_backend_limits(self):
        from scpf.core import Box, Faces, Hole
        from scpf.features import compile_features

        plate = Box(40, 30, 10)
        side_hole = Hole(d=4).on(plate, face=Faces.LEFT)
        with self.assertRaisesRegex(
            ValueError, "native placement/topology limitation"
        ):
            compile_features(plate + side_hole, "Plate")

    def test_face_boundary_selector_requires_faces(self):
        from scpf.core import Edges

        with self.assertRaisesRegex(ValueError, "one or more Faces"):
            Edges.from_faces()

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
