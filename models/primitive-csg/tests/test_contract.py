"""Qualification tests for the primitive CSG case."""
from pathlib import Path
import unittest

from scpf.core import Anchor, Axis, Cylinder, Sphere

BOTTOM = Anchor.BOTTOM
LEFT = Anchor.LEFT
from scpf.compiler import compile_model
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class PrimitiveCsgCommandTests(unittest.TestCase):
    def test_generated_command_contract(self):
        commands = run_script(
            ROOT / "models/primitive-csg/scpf/model.py"
        )["commands"]

        self.assertEqual(
            [command["command"] for command in commands],
            ["solid.sphere", "solid.box", "solid.cylinder", "solid.box"],
        )

        sphere = commands[0]["params"]
        joined_box = commands[1]["params"]
        cylinder = commands[2]["params"]
        clipped_box = commands[3]["params"]

        self.assertEqual(sphere["operation"], "new")
        self.assertEqual(sphere["radius"], 20)
        self.assertEqual(sphere["center"], [0, 0, 0])
        self.assertEqual(joined_box["operation"], "join")
        self.assertEqual(joined_box["center"], [18.0, 0.0, 10.0])

        self.assertEqual(cylinder["operation"], "cut")
        self.assertEqual(cylinder["axis"], "X")
        self.assertEqual(cylinder["diameter"], 8)
        self.assertEqual(cylinder["height"], 60)
        self.assertEqual(cylinder["base"], [-30, 0, 0])

        self.assertEqual(clipped_box["operation"], "intersect")
        self.assertEqual(clipped_box["center"], [0.0, 0.0, 15.0])

    def test_explicit_primitive_anchors_choose_native_datums(self):
        bottom = compile_model(
            Cylinder(d=8, h=20, anchor=BOTTOM),
            "BottomCylinder",
        )["commands"][-1]["params"]
        self.assertEqual(bottom["base"], [0, 0, 0])

        left = compile_model(
            Cylinder(d=8, h=20, axis=Axis.X, anchor=LEFT),
            "LeftCylinder",
        )["commands"][-1]["params"]
        self.assertEqual(left["base"], [0, 0, 0])

        sphere = compile_model(
            Sphere(10, anchor=LEFT),
            "LeftSphere",
        )["commands"][-1]["params"]
        self.assertEqual(sphere["center"], [10, 0, 0])


if __name__ == "__main__":
    unittest.main()
