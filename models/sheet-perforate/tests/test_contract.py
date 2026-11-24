"""Command contract for the #779 native sheet-perforation case."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-perforate/scpf/model.py"


class SheetPerforateContractTests(unittest.TestCase):
    def test_perforation_uses_native_sheet_history(self):
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
                "sheet.perforate",
            ],
        )

        perforate = geometry[-1]["params"]
        self.assertEqual(
            perforate,
            {
                "diameter": "perforation_diameter",
                "pitch": "perforation_pitch",
                "body": "SheetPerforate",
                "margin": "perforation_margin",
                "pattern": "square",
            },
        )
        self.assertNotIn("sketch", perforate)
        self.assertNotIn("profiles", perforate)

    def test_perforation_parameters_keep_length_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["perforation_diameter"], "mm")
        self.assertEqual(units["perforation_pitch"], "mm")
        self.assertEqual(units["perforation_margin"], "mm")


if __name__ == "__main__":
    unittest.main()
