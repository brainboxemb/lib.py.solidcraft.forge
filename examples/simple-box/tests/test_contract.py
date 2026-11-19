"""Integration contract for native parameterized Box lowering."""

import json
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples/simple-box"
MODEL = EXAMPLE / "scpf/model.py"
MUTATION = EXAMPLE / "verification/change_length.json"


class SimpleBoxCommandTests(unittest.TestCase):
    def test_saved_design_mutation_changes_length_parameter(self):
        document = json.loads(MUTATION.read_text(encoding="utf-8"))
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
        commands = run_script(MODEL)["commands"]

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
