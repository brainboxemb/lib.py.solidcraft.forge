"""Explicit Sketch contract tests."""
import unittest

from scpf import Sketch

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
