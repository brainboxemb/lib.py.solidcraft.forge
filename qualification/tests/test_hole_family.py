"""Qualification command contract for the native Hole family."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/hole-family/scpf/model.py"


class HoleFamilyQualificationTests(unittest.TestCase):
    def test_hole_family_uses_four_native_hole_features(self):
        document = run_script(MODEL)
        commands = document["commands"]

        holes = [
            row["params"]
            for row in commands
            if row["command"] == "solid.hole"
        ]
        self.assertEqual(len(holes), 4)
        self.assertFalse(
            any(row["command"].startswith("sketch.") for row in commands)
        )
        self.assertEqual(
            [row["position"] for row in holes],
            [
                [-45, 0, "thickness"],
                [-15, 0, "thickness"],
                [15, 0, "thickness"],
                [45, 0, "thickness"],
            ],
        )
        self.assertTrue(
            all(row["direction"] == [0, 0, -1] for row in holes)
        )
        self.assertTrue(
            all(row["targets"] == ["HoleFamily"] for row in holes)
        )

        self.assertEqual(holes[0]["diameter"], 6)
        self.assertNotIn("type", holes[0])

        self.assertEqual(
            {
                "type": holes[1]["type"],
                "diameter": holes[1]["diameter"],
                "cb_diameter": holes[1]["cb_diameter"],
                "cb_depth": holes[1]["cb_depth"],
            },
            {
                "type": "counterbore",
                "diameter": 6,
                "cb_diameter": 12,
                "cb_depth": 4,
            },
        )
        self.assertEqual(
            {
                "type": holes[2]["type"],
                "diameter": holes[2]["diameter"],
                "cs_diameter": holes[2]["cs_diameter"],
                "cs_angle": holes[2]["cs_angle"],
            },
            {
                "type": "countersink",
                "diameter": 6,
                "cs_diameter": 12,
                "cs_angle": 90,
            },
        )
        self.assertEqual(holes[3]["diameter"], 5)
        self.assertEqual(holes[3]["thread"], "M6")
        self.assertEqual(holes[3]["thread_depth"], 10)
        self.assertTrue(holes[3]["modeled"])
        self.assertEqual(holes[3]["ease_out"], "short")


if __name__ == "__main__":
    unittest.main()
