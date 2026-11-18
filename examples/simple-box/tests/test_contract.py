"""Qualification contract for native parameterized Box lowering."""

from pathlib import Path
import json
import unittest

from scpf.runner import run_script
from qualification.cases import QUALIFICATION_CASES
from qualification.native_cases import mutation_spec


ROOT = Path(__file__).resolve().parents[3]


class SimpleBoxCommandTests(unittest.TestCase):
    def test_editable_box_requires_q5_saved_design_mutation(self):
        case = next(
            case for case in QUALIFICATION_CASES
            if case["slug"] == "simple-box"
        )
        self.assertTrue(case["q5_required"])
        spec = mutation_spec("simple-box")
        document = json.loads(
            (ROOT / spec["command"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            document["commands"],
            [{
                "command": "parameters.change",
                "params": {
                    "name": "length",
                    "expression": "50 mm",
                },
            }],
        )

    def test_box_lowers_directly_to_native_solid_box(self):
        commands = run_script(
            ROOT / "examples/simple-box/scpf/model.py"
        )["commands"]

        feature_commands = [
            row for row in commands
            if row["command"] != "parameters.add"
        ]
        self.assertEqual(
            [row["command"] for row in feature_commands],
            ["solid.box"],
        )

        box = feature_commands[0]["params"]
        self.assertEqual(box["length"], "length")
        self.assertEqual(box["width"], "width")
        self.assertEqual(box["height"], "height")
        self.assertEqual(
            box["corner"],
            ["-length / 2", "-width / 2", 0],
        )

        self.assertFalse(
            any(row["command"].startswith("sketch.") for row in commands)
        )
        self.assertFalse(
            any(row["command"] == "solid.extrude" for row in commands)
        )


if __name__ == "__main__":
    unittest.main()
