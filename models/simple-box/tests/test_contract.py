"""Integration contract for native parameterized Box lowering."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/simple-box/scpf/model.py"


class SimpleBoxCommandTests(unittest.TestCase):
    def test_same_source_lowers_to_native_mitcad_box(self):
        document = run_script(MODEL, backend="mitcad")
        self.assertEqual(document["format"], "scpf-mitcad")
        self.assertEqual(
            [row["cmd"] for row in document["commands"]],
            ["add_parameter", "add_parameter", "add_parameter", "add_feature"],
        )
        box = document["commands"][-1]
        self.assertEqual(box["name"], "SimpleBox")
        self.assertEqual(box["def"]["type"], "box")
        self.assertEqual(box["def"]["corner"], ["-(length / 2)", "-(width / 2)"])
        self.assertEqual(box["def"]["height"], "height")

    def test_box_lowers_directly_to_native_solid_box(self):
        """Keep the representative simple-box lowering contract explicit."""

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
