"""Command contract for the #773 native sheet-hem fixture."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-hem/scpf/model.py"


class SheetHemContractTests(unittest.TestCase):
    def test_hem_uses_native_sheet_history_and_rule_inheritance(self):
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
                "sheet.hem",
            ],
        )

        base = geometry[4]["params"]
        self.assertEqual(base["type"], "base")
        self.assertEqual(base["rule"], "Hem Rule")

        hem = geometry[5]["params"]
        self.assertEqual(
            hem,
            {
                "edges": [[40.0, 0.0, 2.0]],
                "length": "hem_length",
                "gap": "hem_gap",
                "body": "SheetHem",
            },
        )
        self.assertNotIn("thickness", hem)
        self.assertNotIn("k_factor", hem)
        self.assertNotIn("radius", hem)

    def test_hem_parameters_keep_length_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["hem_length"], "mm")
        self.assertEqual(units["hem_gap"], "mm")


if __name__ == "__main__":
    unittest.main()
