"""Q2 command contract for anchored-holes."""

from pathlib import Path
import unittest

from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_anchored_holes_command_contract(self):
        rows = run_script(ROOT / "examples/anchored-holes/scpf/model.py")["commands"]
        self.assertEqual([row["params"]["name"] for row in rows if row["command"] == "sketch.create"], ["Base", "Hole"])
        circles = [row["params"] for row in rows if row["command"] == "sketch.circle.center"]
        self.assertEqual(len(circles), 1)
        self.assertEqual(circles[0]["diameter"], 8)
        self.assertEqual(circles[0]["center"], ["(width / 2)", "((depth - (spacing)) / 2)"])
        cuts = [row["params"] for row in rows if row["command"] == "solid.extrude" and row["params"].get("operation") == "cut"]
        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0]["name"], "Hole")
        patterns = [row["params"] for row in rows if row["command"] == "solid.pattern.rectangular"]
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0], {"features": ["Hole"], "dir1": [0.0, 1.0, 0.0], "count1": 2, "spacing1": "spacing", "alignment": "right", "reversed": False})


if __name__ == "__main__":
    unittest.main()
