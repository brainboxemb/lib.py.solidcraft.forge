"""Command-contract checks for the attached Polygon2D regression fixture."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[1]


class AttachedThroughAllContractTests(unittest.TestCase):
    def test_polygon_is_closed_and_cut_through_all(self):
        commands = run_script(ROOT / "scpf" / "model.py")["commands"]
        polygon = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.line"
        )
        self.assertTrue(polygon["closed"])
        self.assertEqual(len(polygon["points"]), 4)

        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(extrude["operation"], "cut")
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")


if __name__ == "__main__":
    unittest.main()
