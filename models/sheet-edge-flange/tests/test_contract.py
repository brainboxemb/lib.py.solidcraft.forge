"""Command contract for the #682 native edge-flange fixture."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-edge-flange/scpf/model.py"


class SheetEdgeFlangeContractTests(unittest.TestCase):
    def test_edge_flange_uses_native_sheet_history_and_rule_inheritance(self):
        commands = run_script(MODEL)["commands"]
        geometry = [
            row for row in commands
            if row["command"] != "parameters.add"
        ]

        self.assertEqual(
            [row["command"] for row in geometry],
            [
                "sheet.manage_rules",
                "sketch.create",
                "sketch.rectangle.two_point",
                "sketch.finish",
                "sheet.flange",
                "sheet.flange",
            ],
        )

        base = geometry[4]["params"]
        self.assertEqual(base["type"], "base")
        self.assertEqual(base["rule"], "Edge Flange Rule")

        edge = geometry[5]["params"]
        self.assertEqual(
            edge,
            {
                "type": "edge",
                "edges": [[40.0, 0.0, 2.0]],
                "height": "flange_height",
                "angle": "flange_angle",
                "body": "SheetEdgeFlange",
            },
        )
        self.assertNotIn("thickness", edge)
        self.assertNotIn("k_factor", edge)
        self.assertNotIn("radius", edge)

    def test_flange_parameters_keep_length_and_angle_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["flange_height"], "mm")
        self.assertEqual(units["flange_angle"], "deg")


if __name__ == "__main__":
    unittest.main()
