"""Qualification contract for explicit RoundedRectangle2D sketches."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class RoundedRectangleSketchCommandTests(unittest.TestCase):
    def test_named_sketch_uses_native_rounded_rectangle(self):
        commands = run_script(
            ROOT / "models/rounded-rectangle-sketch/scpf/model.py"
        )["commands"]

        rounded = [
            row["params"]
            for row in commands
            if row["command"] == "sketch.rectangle.rounded"
        ]
        self.assertEqual(len(rounded), 1)
        self.assertEqual(rounded[0]["radius"], "radius")
        self.assertIn("pad_width", rounded[0]["p0"][0])
        self.assertIn("pad_width", rounded[0]["p1"][0])
        self.assertIn("pad_depth", rounded[0]["p0"][1])
        self.assertIn("pad_depth", rounded[0]["p1"][1])
        self.assertNotEqual(rounded[0]["p0"], [-20, -15])

        sketches = [
            row["params"].get("name")
            for row in commands
            if row["command"] == "sketch.create"
        ]
        self.assertIn("Rounded pad", sketches)

        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
            and row["params"].get("name") == "Rounded pad"
        )
        self.assertEqual(extrude["distance"], "pad_height")
        self.assertEqual(extrude["direction"], "positive")
        self.assertEqual(extrude["operation"], "join")

        world_sketch = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
            and row["params"].get("name") == "World cut"
        )
        self.assertEqual(world_sketch["plane"], "YZ")

        rectangle = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.rectangle.two_point"
        )
        self.assertIn("cut_y", str(rectangle["p0"][0]))
        self.assertIn("cut_width", str(rectangle["p0"][0]))
        self.assertIn("cut_z", str(rectangle["p0"][1]))
        self.assertIn("cut_height", str(rectangle["p0"][1]))

        cut = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
            and row["params"].get("operation") == "cut"
        )
        self.assertEqual(cut["distance"], "cut_length")
        self.assertEqual(cut["direction"], "symmetric")
        self.assertEqual(len(cut["targets"]), 1)
        self.assertNotIn("body_name", cut)


if __name__ == "__main__":
    unittest.main()
