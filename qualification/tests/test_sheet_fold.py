"""Q2 command contract for the native sheet-fold qualification."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/sheet-fold/scpf/model.py"


class SheetFoldQualificationTests(unittest.TestCase):
    def test_sheet_fold_uses_native_sheet_history(self):
        document = run_script(MODEL)
        commands = document["commands"]

        geometry_commands = [
            row["command"]
            for row in commands
            if row["command"] != "parameters.add"
        ]
        self.assertEqual(
            geometry_commands,
            [
                "sheet.manage_rules",
                "sketch.create",
                "sketch.rectangle.two_point",
                "sketch.finish",
                "sheet.flange",
                "solid.hole",
                "sheet.fold",
            ],
        )
        self.assertNotIn("solid.extrude", geometry_commands)

        rule = next(
            row["params"]
            for row in commands
            if row["command"] == "sheet.manage_rules"
        )
        self.assertEqual(rule["name"], "SheetFold Rule")
        self.assertEqual(rule["thickness"], "thickness")
        self.assertEqual(rule["bend_radius"], "bend_radius")
        self.assertEqual(rule["k_factor"], "k_factor")

        base = next(
            row["params"]
            for row in commands
            if row["command"] == "sheet.flange"
        )
        self.assertEqual(
            base,
            {
                "type": "base",
                "sketch": "Blank",
                "rule": "SheetFold Rule",
                "body_name": "SheetFold",
            },
        )

        hole = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.hole"
        )
        self.assertEqual(hole["diameter"], "hole_diameter")
        self.assertEqual(hole["position"], [-20, 0, "thickness"])
        self.assertEqual(hole["direction"], [0.0, 0.0, -1.0])
        self.assertEqual(hole["targets"], ["SheetFold"])

        fold = next(
            row["params"]
            for row in commands
            if row["command"] == "sheet.fold"
        )
        self.assertEqual(
            fold,
            {
                "points": [[20, -20, 0], [20, 20, 0]],
                "angle": "fold_angle",
                "position": "centerline",
                "flip": False,
                "body": "SheetFold",
                "fixed": [-20, 0, 0],
            },
        )

    def test_sheet_rule_and_fold_parameters_have_native_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["thickness"], "mm")
        self.assertEqual(units["bend_radius"], "mm")
        self.assertEqual(units["k_factor"], "")
        self.assertEqual(units["fold_angle"], "deg")


if __name__ == "__main__":
    unittest.main()
