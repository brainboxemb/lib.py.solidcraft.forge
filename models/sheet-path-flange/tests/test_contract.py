"""Command contract for the #776 native sheet-path-flange fixture."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-path-flange/scpf/model.py"


class SheetPathFlangeContractTests(unittest.TestCase):
    def test_path_flange_uses_native_sheet_and_open_chain_history(self):
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
                "sketch.create",
                "sketch.line",
                "sketch.finish",
                "sheet.path_flange",
            ],
        )

        line = geometry[6]
        self.assertEqual(
            line["bind"],
            {"$contour_curves_1": "curves"},
        )

        path_flange = geometry[-1]["params"]
        self.assertEqual(
            path_flange,
            {
                "edge": [40.0, 0.0, 2.0],
                "sketch": "Path",
                "curves": "$contour_curves_1",
                "body": "SheetPathFlange",
                "radius": "path_radius",
            },
        )
        self.assertNotIn("thickness", path_flange)
        self.assertNotIn("k_factor", path_flange)

    def test_path_flange_parameters_keep_length_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["path_height"], "mm")
        self.assertEqual(units["path_radius"], "mm")


if __name__ == "__main__":
    unittest.main()
