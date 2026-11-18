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

class GeometryPrimitives(unittest.TestCase):
    def test_cylinder_keyword_form_is_direct_3d_primitive(self):
        from scpf.core import Cylinder
        self.assertEqual(Cylinder(d=24, h=14).kind, "cylinder")
        self.assertEqual(Cylinder(d=24, h=14).at(40, 25, 8).kind, "placed3d")

    def test_cylinder_axis_lowers_directly_to_native_axis(self):
        from scpf.compiler import compile_model
        from scpf.core import Axis, Cylinder

        commands = compile_model(
            Cylinder(d=12, h=30, axis=Axis.X).at(0, 0, 0),
            "Pin",
        )["commands"]
        cylinder = commands[-1]
        self.assertEqual(cylinder["command"], "solid.cylinder")
        self.assertEqual(cylinder["params"]["axis"], "X")
        self.assertEqual(cylinder["params"]["base"], [-15, 0, 0])

        with self.assertRaisesRegex(ValueError, "Cylinder axis"):
            Cylinder(d=12, h=30, axis="diagonal")

    def test_cylinder_at_places_center_on_centered_csg_body(self):
        from scpf.compiler import compile_model
        from scpf.core import Anchor, Axis, Box, Cylinder, Parameter, Sphere

        size = Parameter("size", 50)
        body = Sphere(size / 1.5) & Box(
            size, size, size
        )
        diameter = size / 1.5

        holes = (
            Cylinder(d=diameter, h=size, axis=Axis.X).at(body)
            + Cylinder(d=diameter, h=size, axis=Axis.Y).at(body)
            + Cylinder(d=diameter, h=size, axis=Axis.Z).at(body)
        )
        commands = compile_model(body - holes, "CsgCube")["commands"]

        cylinders = [
            command["params"]
            for command in commands
            if command["command"] == "solid.cylinder"
        ]
        self.assertEqual([item["axis"] for item in cylinders], ["X", "Y", "Z"])
        self.assertEqual(
            [item["base"] for item in cylinders],
            [
                ["-(size / 2)", 0, 0],
                [0, "-(size / 2)", 0],
                [0, 0, "-(size / 2)"],
            ],
        )

        with self.assertRaisesRegex(ValueError, "CENTER-to-CENTER"):
            Cylinder(d=10, h=20).at(
                body,
                anchor=Anchor.TOP,
                child=Anchor.CENTER,
            )

    def test_cylinder_standalone_native_command(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "model.py"
            script.write_text(
                "@dataclass\n"
                "class Pin:\n"
                "    diameter: float = 12\n"
                "    def build(self):\n"
                "        Cylinder(d=self.diameter, h=20).at(10, 5, 3, anchor=Anchor.BOTTOM)\n"
                "Pin()\n"
            )
            commands = run_script(script)["commands"]
        cylinder = commands[-1]
        self.assertEqual(cylinder["command"], "solid.cylinder")
        self.assertEqual(cylinder["params"]["base"], [10, 5, 3])
        self.assertEqual(cylinder["params"]["diameter"], "diameter")
        self.assertEqual(cylinder["params"]["operation"], "new")

    def test_move_translates_a_csg_composite_without_changing_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def CsgCube(size=50.0):\n"
                "    body = Sphere(size / 1.5) & Box(size, size, size)\n"
                "    hole = Cylinder(d=size / 1.5, h=size).move(z=-10)\n"
                "    return (body - hole).move(x=10, y=20, z=30)\n"
                "CsgCube()\n"
            )
            document = run_script(file)
        commands = document["commands"]
        self.assertEqual(commands[1]["params"]["center"], [10, 20, 30])
        self.assertEqual(commands[2]["params"]["center"], [10, 20, 30])
        self.assertEqual(commands[3]["params"]["base"][:2], [10, 20])
        self.assertIn("size / 2", str(commands[3]["params"]["base"][2]))
        self.assertIn("20 mm", str(commands[3]["params"]["base"][2]))
        self.assertEqual(commands[3]["params"]["axis"], "Z")

    def test_all_standard_solids_use_centered_origin_in_native_and_csg(self):
        from scpf import BOTTOM, FRONT, LEFT, Axis, Box, Cylinder, Sphere
        from scpf.compiler import compile_model

        # Feature-tree and CSG lowering must compute exactly the same native
        # base for a Cylinder. No implicit bottom-vs-center difference.
        cases = (
            (Cylinder(d=8, h=20), [0, 0, -10]),
            (Cylinder(d=8, h=20, anchor=BOTTOM), [0, 0, 0]),
            (Cylinder(d=8, h=20, axis=Axis.X), [-10, 0, 0]),
            (Cylinder(d=8, h=20, axis=Axis.X, anchor=LEFT), [0, 0, 0]),
            (Cylinder(d=8, h=20, axis=Axis.Y, anchor=FRONT), [0, 0, 0]),
            (Cylinder(d=8, h=20).at(5, 6, 7), [5, 6, -3]),
            (Cylinder(d=8, h=20).at(5, 6, 7, anchor=BOTTOM), [5, 6, 7]),
        )
        for cylinder, expected in cases:
            with self.subTest(cylinder=cylinder):
                native = compile_model(Box(50, 50, 50) - cylinder, "Native")["commands"]
                csg = compile_model(
                    (Box(50, 50, 50) & Sphere(40)) - cylinder,
                    "CSG",
                )["commands"]
                native_cyl = next(
                    row["params"] for row in native
                    if row["command"] == "solid.cylinder"
                )
                csg_cyl = next(
                    row["params"] for row in csg
                    if row["command"] == "solid.cylinder"
                )
                self.assertEqual(native_cyl["base"], expected)
                self.assertEqual(csg_cyl["base"], expected)
                self.assertEqual(native_cyl["axis"], csg_cyl["axis"])

        centered = compile_model(Sphere(10), "Sphere")["commands"]
        self.assertEqual(centered[-1]["params"]["center"], [0, 0, 0])
        offset = compile_model(Sphere(10, anchor=LEFT), "Sphere")["commands"]
        self.assertEqual(offset[-1]["params"]["center"], [10, 0, 0])
        moved = compile_model(Sphere(10).at(5, 6, 7), "Sphere")["commands"]
        self.assertEqual(moved[-1]["params"]["center"], [5, 6, 7])

    def test_cylinder_symbolic_height_keeps_center_after_parameter_change(self):
        from scpf import Box, Cylinder, Parameter
        from scpf.compiler import compile_model

        height = Parameter("height", 20)
        commands = compile_model(
            Box(50, 50, 50) - Cylinder(d=8, h=height),
            "Parametric",
        )["commands"]
        cylinder = next(
            row["params"] for row in commands
            if row["command"] == "solid.cylinder"
        )
        self.assertIn("height", str(cylinder["base"][2]))
        self.assertNotEqual(cylinder["base"][2], -10)

    def test_cylinder_has_no_type_specific_orient_shortcut(self):
        from scpf.core import Cylinder
        self.assertFalse(hasattr(Cylinder(d=8, h=20), "orient"))

    def test_cone_is_native_tapered_primitive(self):
        from scpf import BOTTOM, Cone, Parameter
        from scpf.compiler import compile_model

        diameter = Parameter("diameter", 20)
        interference = Parameter("interference", 0.2)
        commands = compile_model(
            Cone(
                d=diameter,
                top_d=diameter + interference,
                h=20,
                anchor=BOTTOM,
            ),
            "TaperedPin",
        )["commands"]
        cone = next(
            row["params"] for row in commands
            if row["command"] == "solid.cone"
        )
        self.assertEqual(cone["base"], [0, 0, 0])
        self.assertEqual(cone["diameter"], "diameter")
        self.assertIn("interference", str(cone["top_diameter"]))
        self.assertEqual(cone["height"], 20)

    def test_cone_supports_only_center_or_axial_end_anchors(self):
        from scpf import BOTTOM, LEFT, Axis, Cone
        from scpf.compiler import compile_model

        bottom = compile_model(
            Cone(d=20, top_d=21, h=20, anchor=BOTTOM),
            "Cone",
        )["commands"][-1]["params"]
        self.assertEqual(bottom["base"], [0, 0, 0])

        x_axis = compile_model(
            Cone(d=20, top_d=21, h=20, axis=Axis.X, anchor=LEFT),
            "ConeX",
        )["commands"][-1]["params"]
        self.assertEqual(x_axis["base"], [0, 0, 0])
        self.assertEqual(x_axis["axis"], "X")

        with self.assertRaisesRegex(ValueError, "axial end"):
            Cone(d=20, top_d=21, h=20, anchor=LEFT)

    def test_move_rejects_non_finite_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def Cuboid(size=50):\n"
                "    return Box(size, size, size).move(x=float('nan'))\n"
                "Cuboid()\n"
            )
            with self.assertRaises(ValueError):
                run_script(file)

    def test_box_default_is_native_center_and_bottom_is_explicit(self):
        from scpf import BOTTOM, CENTER, Box
        from scpf.compiler import compile_model

        default = compile_model(Box(40, 30, 10), "DefaultBox")["commands"]
        default_box = next(
            row["params"] for row in default
            if row["command"] == "solid.box"
        )
        self.assertEqual(default_box["center"], [0, 0, 0])
        self.assertNotIn("corner", default_box)
        self.assertEqual(Box(40, 30, 10).data[-1].vector, CENTER.vector)

        bottom = compile_model(
            Box(40, 30, 10, anchor=BOTTOM),
            "BottomBox",
        )["commands"]
        bottom_box = next(
            row["params"] for row in bottom
            if row["command"] == "solid.box"
        )
        self.assertEqual(bottom_box["corner"], [-20.0, -15.0, 0])
        self.assertNotIn("center", bottom_box)

    def test_box_cardinal_anchor_uses_native_corner_datum(self):
        from scpf import BOTTOM, FRONT, Box
        from scpf.compiler import compile_model

        commands = compile_model(
            Box(40, 30, 10, anchor=FRONT + BOTTOM),
            "FrontBottomBox",
        )["commands"]
        box = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.box"
        )
        self.assertEqual(box["corner"], [-20.0, 0, 0])
        self.assertNotIn("center", box)

    def test_csg_box_uses_same_centered_default(self):
        from scpf import BOTTOM, Box, Sphere
        from scpf.compiler import compile_model

        default = compile_model(
            Sphere(20) + Box(10, 10, 10),
            "DefaultCsgBox",
        )["commands"]
        joined_default = next(
            row["params"] for row in default
            if row["command"] == "solid.box"
        )
        self.assertEqual(joined_default["center"], [0, 0, 0])
        self.assertNotIn("corner", joined_default)

        bottom = compile_model(
            Sphere(20) + Box(10, 10, 10, anchor=BOTTOM),
            "BottomCsgBox",
        )["commands"]
        joined_bottom = next(
            row["params"] for row in bottom
            if row["command"] == "solid.box"
        )
        self.assertEqual(joined_bottom["corner"], [-5.0, -5.0, 0])
        self.assertNotIn("center", joined_bottom)

    def test_box_center_tracks_declared_anchor(self):
        from scpf import BOTTOM, Box
        from scpf.core import _shape_center

        self.assertEqual(_shape_center(Box(40, 30, 10)), (0, 0, 0))
        self.assertEqual(
            _shape_center(Box(40, 30, 10, anchor=BOTTOM)),
            (0, 0, 5.0),
        )

    def test_box_at_overrides_constructor_anchor_placement(self):
        from scpf import BOTTOM, Box
        from scpf.compiler import compile_model

        commands = compile_model(
            Box(20, 10, 6).at(
                0, 0, 0, anchor=BOTTOM
            ),
            "PlacedBox",
        )["commands"]
        box = next(
            row["params"] for row in commands
            if row["command"] == "solid.box"
        )
        self.assertEqual(box["corner"], [-10.0, -5.0, 0])
        self.assertNotIn("center", box)

    def test_taper_measures_from_bottom_for_center_and_bottom_anchors(self):
        from scpf import BOTTOM, Box
        from scpf.compiler import compile_model

        centered = compile_model(
            Box(40, 30, 10).taper(from_z=2, inset=1),
            "CenteredTaper",
        )["commands"]
        centered_sketches = [
            row["params"]
            for row in centered
            if row["command"] == "sketch.create"
        ]
        self.assertEqual(
            [row.get("offset", 0) for row in centered_sketches],
            [-5.0, -3.0, 5.0],
        )

        bottom = compile_model(
            Box(40, 30, 10, anchor=BOTTOM).taper(from_z=2, inset=1),
            "BottomTaper",
        )["commands"]
        bottom_sketches = [
            row["params"]
            for row in bottom
            if row["command"] == "sketch.create"
        ]
        self.assertEqual(
            [row.get("offset", 0) for row in bottom_sketches],
            [0, 2, 10],
        )

    def test_parameterized_taper_commands_are_serializable_for_both_origins(self):
        from scpf import Anchor, Box, Parameter
        from scpf.compiler import compile_model

        length = Parameter("length", 159.70)
        width = Parameter("width", 319.71)
        depth = Parameter("depth", 14.50)
        start = Parameter("front_depth", 2.0)
        inset = Parameter("rear_inset", 1.25)

        for anchor in (Anchor.CENTER, Anchor.BOTTOM):
            with self.subTest(anchor=anchor):
                document = compile_model(
                    Box(length, width, depth, anchor=anchor).taper(
                        from_z=start, inset=inset
                    ),
                    "ParametricTaper",
                )
                # This also catches raw Python Expression instances nested
                # inside native sketch p0/p1 lists.
                json.dumps(document)
                rectangles = [
                    row["params"]
                    for row in document["commands"]
                    if row["command"] == "sketch.rectangle.two_point"
                ]
                self.assertEqual(len(rectangles), 3)
                for rectangle in rectangles:
                    for key in ("p0", "p1"):
                        self.assertTrue(all(
                            isinstance(value, (int, float, str))
                            for value in rectangle[key]
                        ))
                self.assertIn("length", str(rectangles[0]["p0"]))
                self.assertIn("width", str(rectangles[0]["p0"]))
                # The rear sketch used to stringify Python's Expression
                # dataclass, yielding invalid SolidCraft syntax such as
                # "Expression(value=..., expression=...) + rear_inset".
                for rectangle in rectangles:
                    for value in (*rectangle["p0"], *rectangle["p1"]):
                        self.assertNotIn("Expression(", str(value))
                        self.assertNotIn("value=", str(value))
                self.assertIn("rear_inset", str(rectangles[2]["p0"]))

    def test_native_box_supports_directional_anchor_and_edge_selectors(self):
        from scpf import BOTTOM, FRONT, LEFT, RIGHT, Box
        from scpf.compiler import compile_model

        body = Box(100, 40, 12).at(
            0,
            10,
            5,
            anchor=FRONT + BOTTOM,
        ).fillet(
            4,
            edges=[
                BOTTOM + LEFT,
                BOTTOM + RIGHT,
            ],
        )

        commands = compile_model(body, "Board")["commands"]
        self.assertFalse(
            any(command["command"].startswith("sketch.") for command in commands)
        )

        box = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.box"
        )
        self.assertEqual(box["corner"], [-50.0, 10, 5])

        fillet = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.fillet"
        )
        self.assertEqual(
            fillet["edges"],
            [
                [-50.0, 30.0, 5.0],
                [50.0, 30.0, 5.0],
            ],
        )

    def test_positioned_box_keeps_symbolic_dimensions(self):
        from scpf import BOTTOM, FRONT, Box, Parameter
        from scpf.compiler import compile_model

        width = Parameter("width", 100)
        depth = Parameter("depth", 40)
        height = Parameter("height", 12)
        x = Parameter("x_position", 20)
        y = Parameter("y_position", 10)
        z = Parameter("z_position", 5)

        commands = compile_model(
            Box(width, depth, height).at(
                x,
                y,
                z,
                anchor=FRONT + BOTTOM,
            ),
            "Board",
        )["commands"]

        box = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.box"
        )
        self.assertEqual(box["length"], "width")
        self.assertEqual(box["width"], "depth")
        self.assertEqual(box["height"], "height")
        self.assertIn("x_position", str(box["corner"][0]))
        self.assertIn("width", str(box["corner"][0]))
        self.assertEqual(box["corner"][1], "y_position")
        self.assertEqual(box["corner"][2], "z_position")
