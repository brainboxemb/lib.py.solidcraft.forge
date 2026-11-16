"""Qualification contract for native parameterized Box lowering."""

from pathlib import Path
import unittest

from scpf.core import Anchor, Box
from scpf.compiler import compile_model
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class SimpleBoxCommandTests(unittest.TestCase):
    def test_box_lowers_directly_to_native_solid_box(self):
        commands = run_script(
            ROOT / "examples/simple-box/scpf/model.py"
        )["commands"]

        feature_commands = [
            row for row in commands
            if row["command"] != "parameters.add"
        ]
        self.assertEqual(
            [row["command"] for row in feature_commands],
            ["solid.box"],
        )

        box = feature_commands[0]["params"]
        self.assertEqual(box["length"], "length")
        self.assertEqual(box["width"], "width")
        self.assertEqual(box["height"], "height")
        self.assertEqual(box["center"], [0, 0, 0])
        self.assertNotIn("corner", box)

        self.assertFalse(
            any(row["command"].startswith("sketch.") for row in commands)
        )
        self.assertFalse(
            any(row["command"] == "solid.extrude" for row in commands)
        )
        self.assertFalse(
            any(
                row["command"] in ("solid.move", "occurrence.move")
                for row in commands
            )
        )

    def test_cardinal_box_anchor_uses_native_corner_datum(self):
        commands = compile_model(
            Box(40, 30, 10, anchor=Anchor.FRONT + Anchor.BOTTOM),
            "FrontBottomBox",
        )["commands"]
        box = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.box"
        )
        self.assertEqual(box["corner"], [-20.0, 0, 0])
        self.assertNotIn("center", box)

    def test_taper_offsets_follow_box_anchor(self):
        centered = compile_model(
            Box(40, 30, 10).taper(from_z=2, inset=1),
            "CenteredTaper",
        )["commands"]
        centered_offsets = [
            row["params"].get("offset", 0)
            for row in centered
            if row["command"] == "sketch.create"
        ]
        self.assertEqual(centered_offsets, [-5.0, -3.0, 5.0])

        bottom = compile_model(
            Box(40, 30, 10, anchor=Anchor.BOTTOM).taper(
                from_z=2,
                inset=1,
            ),
            "BottomTaper",
        )["commands"]
        bottom_offsets = [
            row["params"].get("offset", 0)
            for row in bottom
            if row["command"] == "sketch.create"
        ]
        self.assertEqual(bottom_offsets, [0, 2, 10])


if __name__ == "__main__":
    unittest.main()
