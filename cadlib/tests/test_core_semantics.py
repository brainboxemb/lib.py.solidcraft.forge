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

class CoreSemantics(unittest.TestCase):
    def test_anchor_directions_have_vectors_and_aliases(self):
        from scpf.core import Anchor, AnchorFrame

        self.assertIs(Anchor.UP, Anchor.TOP)
        self.assertIs(Anchor.DOWN, Anchor.BOTTOM)
        self.assertEqual(Anchor.RIGHT.vector, (1.0, 0.0, 0.0))
        self.assertEqual(Anchor.FRONT.vector, (0.0, -1.0, 0.0))
        self.assertEqual(
            Anchor.FRONT_TOP_LEFT.vector,
            (-1.0, -1.0, 1.0),
        )

        frame = AnchorFrame(z=Anchor.BACK, x=Anchor.DOWN)
        self.assertEqual(frame.z, (0.0, 1.0, 0.0))
        self.assertEqual(frame.x, (0.0, 0.0, -1.0))

    def test_cardinal_directions_combine_like_bosl2_selectors(self):
        from scpf import BOTTOM, FRONT, LEFT, RIGHT, TOP

        self.assertEqual((BOTTOM + LEFT).vector, (-1, 0, -1))
        self.assertEqual((TOP + RIGHT).vector, (1, 0, 1))
        self.assertEqual((FRONT + TOP + LEFT).vector, (-1, -1, 1))

        with self.assertRaisesRegex(ValueError, "same axis"):
            _ = LEFT + RIGHT

    def test_cardinal_offset_helpers_preserve_symbolic_dimensions(self):
        from scpf import back, down, front, left, right, up
        from scpf.core import Parameter, command_value

        distance = Parameter("distance", 12)

        self.assertEqual(up(5), (0, 0, 5))
        self.assertEqual(down(5), (0, 0, -5))
        self.assertEqual(left(5), (-5, 0, 0))
        self.assertEqual(right(5), (5, 0, 0))
        self.assertEqual(front(5), (0, -5, 0))
        self.assertEqual(back(5), (0, 5, 0))
        self.assertEqual(command_value(down(distance)[2]), "-(distance)")
        self.assertEqual(command_value(right(distance)[0]), "distance")

    def test_shape_appearance_lowers_without_material_semantics(self):
        from scpf import Box
        from scpf.compiler import compile_model

        document = compile_model(
            Box(40, 30, 10).with_appearance("#ffd21a"),
            "YellowBox",
        )
        commands = document["commands"]
        appearance = next(
            row for row in commands
            if row["command"] == "appearance.assign"
        )

        self.assertEqual(
            appearance["params"],
            {"bodies": ["YellowBox"], "color": "#FFD21A"},
        )
        self.assertFalse(
            any(row["command"].startswith("material.") for row in commands)
        )

    def test_shape_appearance_validates_hex_color(self):
        from scpf import Box

        with self.assertRaisesRegex(ValueError, "#RRGGBB"):
            Box(10, 10, 10).with_appearance("yellow")

    def test_half_and_midpoint_preserve_symbolic_dimensions(self):
        from scpf import half, midpoint
        from scpf.core import Parameter, command_value

        width = Parameter("width", 100)
        left = Parameter("left", 20)
        right = Parameter("right", 80)

        self.assertEqual(half(10), 5)
        self.assertEqual(command_value(half(width)), "width / 2")
        self.assertEqual(
            command_value(midpoint(left, right)),
            "(left + (right)) / 2",
        )
        self.assertEqual(midpoint(10, 20), 15)

    def test_half_helpers_are_available_in_implicit_model_context(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class HalfBox:\n"
                "    width = 80.0\n"
                "    def build(self):\n"
                "        center = midpoint(0, self.width)\n"
                "        offset = down(half(self.width))\n"
                "        return Box(half(self.width), 10, 5).move(x=center, z=offset[2])\n"
                "HalfBox()\n",
                encoding="utf-8",
            )
            generated = run_script(file)

        box = next(
            row["params"] for row in generated["commands"]
            if row["command"] == "solid.box"
        )
        self.assertEqual(box["length"], "width / 2")

    def test_cadmath_preserves_consumer_style_symbolic_dependencies(self):
        from scpf import cadmath
        from scpf.core import Parameter, command_value, parameters_in

        mid_round = Parameter("mid_round", 1.5)
        mid_wall = Parameter("mid_wall", 4.0)
        mid_outer_r = Parameter("mid_outer_r", 12.0)
        mid_size = Parameter("mid_size", 80.0)
        lane_grid = Parameter("lane_grid", 2.5)
        pitch = Parameter("pitch", 4.0)
        margin = Parameter("margin", 5.0)
        mark_width = Parameter("mark_width", 1.0)
        ref_d = Parameter("ref_d", 4.0)
        ref_tip_d = Parameter("ref_tip_d", 2.0)
        ref_tip_h = Parameter("ref_tip_h", 3.0)

        mid_g = cadmath.min(mid_round, mid_wall / 2 - 0.05)
        mid_tip = cadmath.sqrt(
            (mid_outer_r - mid_g) ** 2
            - (mid_outer_r - mid_wall + mid_g) ** 2
        )
        lane = cadmath.round(mid_size / 2 / lane_grid) * lane_grid
        inset = cadmath.floor(
            (mid_size / 2 - margin - mark_width / 2) / (pitch / 2)
        )
        tip_angle = -cadmath.atan(
            (ref_d - ref_tip_d) / (2 * ref_tip_h)
        )
        bounded = cadmath.max(mid_wall, cadmath.abs(-mid_round))

        self.assertIn("min(", command_value(mid_g))
        self.assertIn("sqrt(", command_value(mid_tip))
        self.assertIn("^ 2", command_value(mid_tip))
        self.assertEqual(command_value(lane), "(round((mid_size / 2) / (lane_grid))) * (lane_grid)")
        self.assertIn("floor(", command_value(inset))
        self.assertIn("atan(", command_value(tip_angle))
        self.assertIn("max(", command_value(bounded))
        self.assertIn("abs(", command_value(bounded))
        self.assertEqual(
            {parameter.name for parameter in parameters_in(mid_tip)},
            {"mid_round", "mid_wall", "mid_outer_r"},
        )
        self.assertAlmostEqual(tip_angle.value, -18.43494882292201)

    def test_cadmath_is_available_in_implicit_model_context(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class MathBox:\n"
                "    size = 70.0\n"
                "    limit = 80.0\n"
                "    offset = 20.0\n"
                "    def build(self):\n"
                "        span = cadmath.sqrt(cadmath.min(self.size, self.limit) ** 2 - self.offset ** 2)\n"
                "        return Box(span, 20, 5)\n"
                "MathBox()\n",
                encoding="utf-8",
            )
            generated = run_script(file)

        box = next(
            row["params"] for row in generated["commands"]
            if row["command"] == "solid.box"
        )
        self.assertIn("sqrt(", box["length"])
        self.assertIn("min(size,limit)", box["length"])

    def test_pv_is_explicit_escape_hatch_to_python_value(self):
        from scpf.core import Parameter, pv
        width = Parameter("width", 868.0)
        self.assertEqual(pv(width), 868.0)
        self.assertEqual(pv(width / 2), 434.0)
