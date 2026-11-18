"""Tests migrated from the former test_models.py catch-all."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from scpf.compiler import ModelError
from scpf.runner import run_script
from scpf import Sketch

ROOT = Path(__file__).resolve().parents[2]

class GeometryFeatures(unittest.TestCase):
    def test_anchored_holes_example_compiles_to_one_holes_sketch(self):
        commands = run_script(
            ROOT / "examples/anchored-holes/scpf/model.py")["commands"]
        self.assertEqual(
            [c["params"]["name"] for c in commands
             if c["command"] == "sketch.create"],
            ["Base", "Holes"],
        )
        centers = [
            c["params"]["center"]
            for c in commands
            if c["command"] == "sketch.circle.center"
        ]
        self.assertEqual(len(centers), 2)
        self.assertTrue(all("spacing" in str(center[1]) for center in centers))
        self.assertFalse(any(c["command"] == "solid.hole" for c in commands))
        self.assertEqual(commands[-1]["command"], "solid.extrude")
        self.assertEqual(commands[-1]["params"]["operation"], "cut")

    def test_named_edge_selection_and_explicit_edge_points(self):
        from scpf.core import Box, Edges
        body = Box(80, 50, 8)
        self.assertIs(body.fillet(6).data[2], Edges.VERTICAL)
        self.assertIs(body.fillet(6, edges=Edges.VERTICAL).data[2], Edges.VERTICAL)
        self.assertEqual(body.fillet(6, edges=[(0, 0, 4)]).data[2], [(0, 0, 4)])
        with self.assertRaises(ValueError):
            body.fillet(6, edges="vertical")

    def test_signed_extrude_compiles_to_solidcraft_strings(self):
        from scpf.core import Circle2D, Parameter
        from scpf.compiler import compile_model

        height = Parameter("height", 8)
        with Sketch(plane="XY") as sketch:
            Circle2D(d=8)

        positive = compile_model(
            sketch.extrude(height), "Positive"
        )["commands"][-1]["params"]
        negative = compile_model(
            sketch.extrude(-height), "Negative"
        )["commands"][-1]["params"]
        symmetric = compile_model(
            sketch.extrude(height, sym=True), "Symmetric"
        )["commands"][-1]["params"]

        self.assertEqual((positive["distance"], positive["direction"]), ("height", "positive"))
        self.assertEqual((negative["distance"], negative["direction"]), ("height", "negative"))
        self.assertEqual((symmetric["distance"], symmetric["direction"]), ("height", "symmetric"))

    def test_attached_hole_repeat_builds_one_sketch_cut(self):
        from scpf.core import Axis, Depth, Faces, Hole, Rectangle2D, Parameter
        from scpf.compiler import compile_model
        width = Parameter("width", 100)
        depth = Parameter("depth", 60)
        thickness = Parameter("thickness", 10)
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(width, depth)
        plate = sketch.extrude(thickness)
        holes = Hole(d=8, depth=Depth.THROUGH_ALL).repeat_linear(
            count=2, spacing=40, axis=Axis.Y
        ).on(plate, face=Faces.TOP)
        commands = compile_model(plate + holes, "Plate")["commands"]

        sketches = [c["params"]["name"] for c in commands
                    if c["command"] == "sketch.create"]
        self.assertEqual(sketches, ["Base", "Holes"])
        circles = [c["params"] for c in commands
                   if c["command"] == "sketch.circle.center"]
        centers = [c["center"] for c in circles]
        self.assertEqual(len(centers), 2)
        self.assertTrue(all("width" in str(center[0]) for center in centers))
        self.assertTrue(all("depth" in str(center[1]) for center in centers))
        self.assertTrue(all(c["diameter"] == 8 for c in circles))
        self.assertFalse(any(c["command"] == "solid.hole" for c in commands))
        self.assertEqual(commands[-1]["command"], "solid.extrude")
        self.assertEqual(commands[-1]["params"]["operation"], "cut")
        self.assertEqual(commands[-1]["params"]["direction"], "positive")
        self.assertEqual(commands[-1]["params"]["distance"], "thickness")

    def test_native_rectangular_feature_pattern_command(self):
        from scpf.core import Anchor, Axis, Box, Parameter, Rectangle2D
        from scpf.compiler import compile_model

        columns = Parameter("columns", 3)
        rows = Parameter("rows", 2)
        pitch = Parameter("pitch", 20)
        plate = Box(120, 80, 4, anchor=Anchor.BOTTOM)
        with Sketch(name="Slot", on=plate) as slot:
            Rectangle2D(8, 16)
        cut = slot.extrude(-4)
        plate = plate - cut
        patterned = plate.rectangular_pattern(
            cut,
            count=columns,
            spacing=pitch,
            direction=Axis.X,
            count2=rows,
            spacing2=22,
            direction2=Axis.Y,
        )
        commands = compile_model(patterned, "Plate")["commands"]

        params = {
            command["params"]["name"]: command["params"]
            for command in commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(params["columns"]["unit"], "")
        self.assertEqual(params["rows"]["unit"], "")
        self.assertEqual(params["pitch"]["unit"], "mm")

        pattern = next(
            command for command in commands
            if command["command"] == "solid.pattern.rectangular"
        )
        self.assertEqual(pattern["params"]["features"], ["Slot"])
        self.assertEqual(pattern["params"]["dir1"], [1.0, 0.0, 0.0])
        self.assertEqual(pattern["params"]["count1"], "columns")
        self.assertEqual(pattern["params"]["spacing1"], "pitch")
        self.assertEqual(pattern["params"]["dir2"], [0.0, 1.0, 0.0])
        self.assertEqual(pattern["params"]["count2"], "rows")
        self.assertEqual(pattern["params"]["spacing2"], 22)
        self.assertEqual(
            [c["command"] for c in commands].count("solid.pattern.rectangular"),
            1,
        )

    def test_circular_pattern_emits_one_native_feature_pattern(self):
        from scpf.compiler import compile_model
        from scpf.core import Anchor, Axis, Box, Circle2D, Depth, Parameter

        plate = Box(100, 80, 6, anchor=Anchor.BOTTOM)
        with Sketch(name="BoltHole", on=plate, parent=Anchor.TOP) as bolt:
            bolt.add(Circle2D(d=8), offset=(30, 0))
        cut = bolt.extrude(Depth.THROUGH_ALL)
        plate = plate - cut

        bolts = Parameter("bolts", 6)
        patterned = plate.circular_pattern(
            cut,
            axis=Axis.Z,
            count=bolts,
        )
        commands = compile_model(patterned, "Flange")["commands"]

        parameter = next(
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
            and row["params"]["name"] == "bolts"
        )
        self.assertEqual(parameter["unit"], "")

        patterns = [
            row for row in commands
            if row["command"] == "solid.pattern.circular"
        ]
        self.assertEqual(len(patterns), 1)
        self.assertEqual(
            patterns[0]["params"],
            {
                "features": ["BoltHole"],
                "axis": "Z",
                "count": "bolts",
                "alignment": "right",
                "reversed": False,
            },
        )

    def test_circular_pattern_supports_shifted_axis_and_angle_parameter(self):
        from scpf.compiler import compile_model
        from scpf.core import Anchor, Box, Circle2D, Depth, Parameter

        plate = Box(100, 80, 6, anchor=Anchor.BOTTOM)
        with Sketch(name="BoltHole", on=plate, parent=Anchor.TOP) as bolt:
            bolt.add(Circle2D(d=8), offset=(30, 0))
        cut = bolt.extrude(Depth.THROUGH_ALL)
        plate = plate - cut

        axis_x = Parameter("axis_x", 10)
        sweep = Parameter("sweep", 180)
        patterned = plate.circular_pattern(
            [cut],
            count=4,
            axis=(0, 0, 1),
            origin=(axis_x, 0, 0),
            angle=sweep,
            alignment="center",
            reversed=True,
        )
        commands = compile_model(patterned, "Flange")["commands"]

        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["axis_x"], "mm")
        self.assertEqual(units["sweep"], "deg")

        pattern = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.pattern.circular"
        )
        self.assertEqual(
            pattern,
            {
                "features": ["BoltHole"],
                "axis": {
                    "origin": ["axis_x", 0, 0],
                    "dir": [0.0, 0.0, 1.0],
                },
                "count": 4,
                "angle": "sweep",
                "alignment": "center",
                "reversed": True,
            },
        )

    def test_circular_pattern_validates_shared_feature_and_axis_options(self):
        from scpf.core import Anchor, Axis, Box, Circle2D, Depth

        plate = Box(100, 80, 6, anchor=Anchor.BOTTOM)
        with Sketch(name="BoltHole", on=plate, parent=Anchor.TOP) as bolt:
            bolt.add(Circle2D(d=8), offset=(30, 0))
        cut = bolt.extrude(Depth.THROUGH_ALL)

        with self.assertRaisesRegex(ValueError, "already be applied"):
            plate.circular_pattern(cut, count=6)

        plate = plate - cut
        with self.assertRaisesRegex(ValueError, "positive integer"):
            plate.circular_pattern(cut, count=0)
        with self.assertRaisesRegex(ValueError, "above 0"):
            plate.circular_pattern(cut, count=6, angle=0)
        with self.assertRaisesRegex(ValueError, "at most 360"):
            plate.circular_pattern(cut, count=6, angle=361)
        with self.assertRaisesRegex(ValueError, "non-zero"):
            plate.circular_pattern(cut, count=6, axis=(0, 0, 0))
        with self.assertRaisesRegex(ValueError, "XYZ point"):
            plate.circular_pattern(
                cut,
                count=6,
                axis=Axis.Z,
                origin=(0, 0),
            )
        with self.assertRaisesRegex(ValueError, "alignment"):
            plate.circular_pattern(cut, count=6, alignment="outside")
        with self.assertRaisesRegex(TypeError, "reversed"):
            plate.circular_pattern(cut, count=6, reversed=1)

    def test_rectangular_pattern_requires_applied_extrude_feature(self):
        from scpf.core import Anchor, Box, Rectangle2D

        plate = Box(80, 50, 4, anchor=Anchor.BOTTOM)
        with Sketch(name="Slot", on=plate) as slot:
            Rectangle2D(8, 16)
        cut = slot.extrude(-4)
        with self.assertRaisesRegex(ValueError, "already be applied"):
            plate.rectangular_pattern(cut, count=3, spacing=15)

    def test_old_primitive_pattern_spelling_is_removed(self):
        from scpf.core import Hole
        self.assertFalse(hasattr(Hole(d=8), "pattern"))

    def test_hole_on_starts_at_exterior_top(self):
        from scpf.core import Anchor, Faces, Hole, Rectangle2D
        from scpf.compiler import compile_model, ModelError
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(80, 50)
        plate = sketch.extrude(8)
        attached = Hole(d=8).on(plate, face=Faces.TOP)
        commands = compile_model(plate + attached, "Plate")["commands"]
        self.assertEqual(commands[-1]["command"], "solid.extrude")
        self.assertEqual(commands[-1]["params"]["operation"], "cut")
        with self.assertRaises(ModelError):
            compile_model(
                plate - Hole(d=8).attach(plate, parent=Anchor.CENTER),
                "Plate",
            )
        with self.assertRaises(ValueError):
            Hole(d=-2)

    def test_on_uses_faces_without_exposing_assembly_anchors(self):
        from scpf.core import Anchor, Faces, Hole, Rectangle2D

        with Sketch(name="Base", plane="XY") as sketch:

            Rectangle2D(80, 50)

        plate = sketch.extrude(8)
        top = Hole(d=8).on(plate, face=Faces.TOP)
        bottom = Hole(d=8).on(plate, face=Faces.BOTTOM)

        self.assertEqual(top.kind, "anchored")
        self.assertEqual(bottom.kind, "anchored")
        self.assertIs(top.data[2], Anchor.TOP)
        self.assertIs(bottom.data[2], Anchor.BOTTOM)
        self.assertIs(top.data[3], Anchor.BOTTOM)
        self.assertIs(bottom.data[3], Anchor.BOTTOM)

    def test_symmetric_anchored_cylinder_repeat_follows_plate_dimensions(self):
        from scpf.core import Anchor, Axis, Cylinder, Rectangle2D
        from scpf.compiler import compile_model
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(100, 60)
        base = sketch.extrude(10)
        holes = Cylinder(d=8, h=12).repeat_linear(
            count=2, spacing=40, axis=Axis.Y
        ).attach(base, parent=Anchor.CENTER, child=Anchor.CENTER)
        commands = compile_model(base - holes, "Plate")["commands"]
        cylinders = [c["params"] for c in commands
                     if c["command"] == "solid.cylinder"]
        self.assertEqual(len(cylinders), 2)
        self.assertEqual([c["base"][0] for c in cylinders], [0, 0])
        self.assertEqual([c["base"][1] for c in cylinders], [-20, 20])
        self.assertEqual([c["base"][2] for c in cylinders], [-1, -1])
        self.assertEqual([c["operation"] for c in cylinders], ["cut", "cut"])

    def test_attached_boss_tracks_plate_top_and_offsets(self):
        from scpf.core import Cylinder, Faces, Rectangle2D, Parameter
        from scpf.compiler import compile_model
        width, depth, thickness = (
            Parameter("width", 80), Parameter("depth", 50),
            Parameter("thickness", 8)
        )
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(width, depth)
        base = sketch.extrude(thickness)
        boss = Cylinder(d=24, h=14).on(base, face=Faces.TOP)
        commands = compile_model(base + boss, "Plate")["commands"]
        cylinder = commands[-1]
        self.assertEqual(cylinder["command"], "solid.cylinder")
        self.assertEqual(cylinder["params"]["operation"], "join")
        self.assertEqual(cylinder["params"]["height"], 14)
        self.assertEqual(cylinder["params"]["diameter"], 24)
        self.assertEqual(cylinder["params"]["base"], [0.0, 0.0, 8.0])
        self.assertEqual(
            [row["params"]["name"] for row in commands
             if row["command"] == "sketch.create"],
            ["Base"],
        )

    def test_relative_anchor_rejects_unsupported_usage(self):
        from scpf.core import Anchor, Axis, Cylinder, Rectangle2D, Sphere
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(80, 50)
        base = sketch.extrude(8)
        with self.assertRaises(ValueError):
            Sphere(8).attach(base, parent=Anchor.TOP)
        with self.assertRaises(ValueError):
            Cylinder(d=8, h=10).repeat_linear(count=2, spacing=40, axis=Axis.Z)
        with self.assertRaises(ValueError):
            Cylinder(d=8, h=10).attach(base, offset=(1, 2, 3))

    def test_repeat_linear_requires_explicit_axes_and_valid_count(self):
        from scpf.core import Axis, Cylinder, Hole
        with self.assertRaises(TypeError):
            Hole(d=8).repeat_linear(x=70, y=30)
        with self.assertRaises(ValueError):
            Cylinder(d=8, h=3).repeat_linear(count=0, spacing=40, axis=Axis.X)
        with self.assertRaises(ValueError):
            Hole(d=8).repeat_linear(count=2, spacing=40, axis=Axis.Z)

    def test_attached_hole_uses_sketch_while_explicit_at_can_be_native(self):
        from scpf.compiler import compile_model
        from scpf.core import Box, Rectangle2D, Polygon2D, Hole, Faces
        box = Box(80, 50, 8)
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(80, 50)
        rectangle = sketch.extrude(8)
        for model in (
            box + Hole(d=6).on(box, face=Faces.TOP),
            rectangle + Hole(d=6).on(rectangle, face=Faces.TOP),
        ):
            commands = compile_model(model, "Widget")["commands"]
            self.assertEqual(commands[-1]["command"], "solid.extrude")
            self.assertEqual(commands[-1]["params"]["operation"], "cut")
            self.assertFalse(any(c["command"] == "solid.hole" for c in commands))

        with Sketch(plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (40, 0), (40, 6), (0, 6)], plane="XZ"
            )
        polygon = sketch.extrude(-50)
        commands = compile_model(
            polygon + Hole(d=6).at(20, -25, 0), "Widget"
        )["commands"]
        self.assertEqual(commands[-1]["command"], "solid.hole")

    def test_shell_uses_faces_without_reusing_anchor_semantics(self):
        from scpf.compiler import compile_model
        from scpf.core import Box, Faces
        commands = compile_model(
            Box(80, 50, 30).shell(2, open=Faces.TOP),
            "Enclosure",
        )["commands"]
        self.assertEqual(
            [c["command"] for c in commands],
            [
                "solid.box",
                "solid.shell",
            ],
        )
        self.assertEqual(commands[0]["params"]["body_name"], "Enclosure")
        self.assertEqual(commands[1]["params"]["faces"], [[0, 0, 15]])
        self.assertEqual(commands[1]["params"]["thickness"], 2)
        with self.assertRaises(ValueError):
            Box(80, 50, 30).shell(2, open=Faces.TOP).move(x=10)

    def test_bound_relative_offsets_resolve_against_parent_extents(self):
        from scpf.compiler import compile_model
        from scpf.core import Anchor, Boss, Box, Faces, X, Y
        body = Box(
            80, 50, 30, anchor=Anchor.BOTTOM
        ).shell(2, open=Faces.TOP)

        minimum = Boss(d=7, h=12, hole_d=2.5).attach(
            body,
            parent=Anchor.INNER_BOTTOM,
            offset=(X.MIN + 10, Y.MIN + 10),
        )
        body = body + minimum

        maximum = Boss(d=7, h=12, hole_d=2.5).attach(
            body,
            parent=Anchor.INNER_BOTTOM,
            offset=(X.MAX - 10, Y.MAX - 10),
        )
        body = body + maximum

        commands = compile_model(body, "Enclosure")["commands"]
        bosses = [c for c in commands if c["command"] == "plastic.boss"]
        self.assertEqual(
            [boss["params"]["position"] for boss in bosses],
            [[-30, -15, 2], [30, 15, 2]],
        )

    def test_bound_relative_offsets_reject_wrong_axis(self):
        from scpf.core import Anchor, Boss, Box, Faces, X, Y
        body = Box(
            80, 50, 30, anchor=Anchor.BOTTOM
        ).shell(2, open=Faces.TOP)
        with self.assertRaisesRegex(ValueError, "requires X bounds"):
            Boss(d=7, h=12, hole_d=2.5).attach(
                body,
                parent=Anchor.INNER_BOTTOM,
                offset=(Y.MIN + 10, Y.MIN + 10),
            )
        with self.assertRaisesRegex(ValueError, "requires Y bounds"):
            Boss(d=7, h=12, hole_d=2.5).attach(
                body,
                parent=Anchor.INNER_BOTTOM,
                offset=(X.MIN + 10, X.MIN + 10),
            )

    def test_inner_bottom_anchor_requires_shell(self):
        from scpf.compiler import compile_model, ModelError
        from scpf.core import Anchor, Boss, Box
        body = Box(80, 50, 30)
        boss = Boss(d=7, h=12, hole_d=2.5).attach(
            body,
            parent=Anchor.INNER_BOTTOM,
        )
        with self.assertRaises(ModelError):
            compile_model(body + boss, "Enclosure")

    def test_rounded_rectangle_sketch_compiles_to_true_native_arcs(self):
        from scpf.core import Anchor, Box, RoundedRectangle2D
        from scpf.explicit_sketch import Sketch
        from scpf.compiler import compile_model

        panel = Box(
            159.7, 319.71, 14.5, anchor=Anchor.BOTTOM
        ).taper(from_z=2, inset=1.25)
        with Sketch(name="Rounded rear bays", on=panel) as bays:
            for y in (-120, -40, 40, 120):
                bays.add(
                    RoundedRectangle2D(134.7, 59, 5),
                    offset=(0, y),
                )
        panel = panel - bays.extrude(-12.5)
        commands = compile_model(panel, "Panel")["commands"]
        rounded = [cmd["params"] for cmd in commands
                   if cmd["command"] == "sketch.rectangle.rounded"]
        self.assertEqual(len(rounded), 4)
        self.assertTrue(all(part["radius"] == 5 for part in rounded))
        self.assertEqual(rounded[0]["p0"], [-67.35, -149.5])
        self.assertEqual(rounded[3]["p1"], [67.35, 149.5])
        self.assertEqual([cmd["command"] for cmd in commands].count("solid.loft"), 1)
        self.assertEqual(commands[-1]["params"]["operation"], "cut")

        for size in ((100, 60, 0), (100, 60, 30), (100, 60, -1),
                     (100, 60, 31), (0, 60, 5)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                RoundedRectangle2D(*size)

    def test_explicit_rear_bay_sketch_on_tapered_box(self):
        """Four rear window pockets retain the front plate and the editable loft."""
        from scpf.core import Anchor, Box, Rectangle2D
        from scpf.explicit_sketch import Sketch
        from scpf.compiler import compile_model

        panel = Box(
            159.7, 319.71, 14.5, anchor=Anchor.BOTTOM
        ).taper(from_z=2, inset=1.25)
        with Sketch(name="Rear electronics bays", on=panel, plane="XY",
                    origin=(0, 0, 14.5)) as rear:
            for center_y in (-120, -40, 40, 120):
                rear.add(
                    Rectangle2D(134.7, 60.0),
                    offset=(0, center_y),
                )
        panel = panel - rear.extrude(-12.5)
        commands = compile_model(panel, "Panel")["commands"]
        names = [cmd["command"] for cmd in commands]
        self.assertEqual(names.count("solid.loft"), 1)
        self.assertEqual(names.count("sketch.rectangle.two_point"), 7)
        pocket = next(i for i, cmd in enumerate(commands)
                      if cmd["command"] == "sketch.create"
                      and cmd["params"]["name"] == "Rear electronics bays")
        sketch = commands[pocket]["params"]
        self.assertEqual(sketch["plane"]["origin"], [0, 0, 14.5])
        rectangles = [cmd for cmd in commands[pocket + 1:]
                      if cmd["command"] == "sketch.rectangle.two_point"]
        self.assertEqual(len(rectangles), 4)
        self.assertEqual(rectangles[0]["params"]["p0"], [-67.35, -150])
        self.assertEqual(rectangles[-1]["params"]["p1"], [67.35, 150])
        self.assertEqual(commands[-1]["command"], "solid.extrude")
        self.assertEqual(commands[-1]["params"]["operation"], "cut")
        self.assertEqual(commands[-1]["params"]["direction"], "negative")
        self.assertEqual(commands[-1]["params"]["distance"], 12.5)

    def test_explicit_sketch_scope_requires_profiles_and_closes_before_extrude(self):
        from scpf.core import Box, Circle2D
        from scpf.explicit_sketch import Sketch

        body = Box(40, 30, 6)
        with self.assertRaisesRegex(ValueError, "at least one profile"):
            with Sketch(name="Empty", on=body):
                pass

        sketch = Sketch(name="Pad", on=body)
        with sketch:
            sketch.add(Circle2D(d=10))
            with self.assertRaisesRegex(ValueError, "before extruding"):
                sketch.extrude(5)

        self.assertEqual(sketch.extrude(5).kind, "explicit_sketch_extrusion")

    def test_circle_profile_extrudes_with_explicit_sketch(self):
        from scpf.compiler import compile_model
        from scpf.core import Circle2D
        with Sketch(plane="XY") as sketch:
            Circle2D(d=12)
        commands = compile_model(sketch.extrude(8), "Pin")["commands"]
        self.assertEqual([c["command"] for c in commands],
                         ["sketch.create", "sketch.circle.center",
                          "sketch.finish", "solid.extrude"])
        self.assertEqual(commands[1]["params"]["diameter"], 12)

    def test_plain_model_fillet_keeps_radius_as_named_parameter(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Board:\n"
                "    width = 868.0\n"
                "    depth = 100.0\n"
                "    thickness = 12.0\n"
                "    corner_radius = 4.0\n"
                "    def build(self):\n"
                "        return Box(self.width, self.depth, self.thickness).fillet(\n"
                "            self.corner_radius, edges=Edges.VERTICAL)\n"
                "Board()\n"
            )
            generated = run_script(file)
        self.assertIn(
            {"command": "parameters.add",
             "params": {"name": "corner_radius", "expression": "4", "unit": "mm"}},
            generated["commands"],
        )
        fillet = next(c for c in generated["commands"]
                      if c["command"] == "solid.fillet")
        self.assertEqual(fillet["params"]["radius"], "corner_radius")
