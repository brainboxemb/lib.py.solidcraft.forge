"""Command-contract checks for the rotated Sketch cutter regression."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[1]


class RotatedSketchCutterContractTests(unittest.TestCase):
    def test_two_rotated_sketch_cutters_use_native_frames(self):
        document = run_script(ROOT / "scpf" / "model.py")
        commands = document["commands"]

        sketches = [
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
        ]
        self.assertEqual(len(sketches), 2)
        self.assertEqual(
            {row["name"] for row in sketches},
            {"Left wedge", "Right wedge"},
        )
        for row in sketches:
            self.assertIsInstance(row["plane"], dict)
            self.assertIn("origin", row["plane"])
            self.assertIn("x_dir", row["plane"])
            self.assertIn("y_dir", row["plane"])

        cuts = [
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
            and row["params"].get("operation") == "cut"
        ]
        self.assertEqual(len(cuts), 2)
        for cut in cuts:
            self.assertEqual(cut["targets"], ["RotatedSketchCutter"])


if __name__ == "__main__":
    unittest.main()
