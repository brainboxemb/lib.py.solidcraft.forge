"""Command contract for the #684 native contour-flange fixture."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-contour-flange/scpf/model.py"


class SheetContourFlangeContractTests(unittest.TestCase):
    def test_contour_flange_uses_native_history_and_runtime_curve_bindings(self):
        document = run_script(MODEL)
        self.assertEqual(document["format"], "scpf-replay")
        self.assertEqual(document["version"], 2)

        commands = document["commands"]
        geometry = [
            row for row in commands
            if row["command"] != "parameters.add"
        ]
        self.assertEqual(
            [row["command"] for row in geometry],
            [
                "sheet.manage_rules",
                "sketch.create",
                "sketch.line",
                "sketch.arc.tangent",
                "sketch.line",
                "sketch.finish",
                "sheet.flange",
            ],
        )

        first_line = geometry[2]
        tangent = geometry[3]
        final_line = geometry[4]
        self.assertEqual(
            first_line["bind"],
            {"$contour_curves_1": "curves"},
        )
        self.assertEqual(
            tangent["bind"],
            {
                "$contour_curves_2": {
                    "field": "curves",
                    "prepend": "$contour_curves_1",
                }
            },
        )
        self.assertEqual(
            final_line["bind"],
            {
                "$contour_curves_3": {
                    "field": "curves",
                    "prepend": "$contour_curves_2",
                }
            },
        )

        flange = geometry[-1]["params"]
        self.assertEqual(
            flange,
            {
                "type": "contour",
                "sketch": "Contour",
                "curves": "$contour_curves_3",
                "distance": "contour_width",
                "rule": "Contour Flange Rule",
                "body_name": "SheetContourFlange",
            },
        )
        self.assertNotIn("thickness", flange)
        self.assertNotIn("k_factor", flange)
        self.assertNotIn("bend_radius", flange)
        self.assertFalse(
            any(row["command"] == "solid.extrude" for row in geometry)
        )

    def test_contour_parameters_keep_native_units(self):
        commands = run_script(MODEL)["commands"]
        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["end_height"], "mm")
        self.assertEqual(units["contour_width"], "mm")
        self.assertEqual(units["thickness"], "mm")
        self.assertEqual(units["bend_radius"], "mm")
        self.assertEqual(units["k_factor"], "")


if __name__ == "__main__":
    unittest.main()
