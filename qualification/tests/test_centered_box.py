"""Qualification contract for native centered Box lowering."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class CenteredBoxCommandTests(unittest.TestCase):
    def test_centered_box_uses_native_center_datum(self):
        commands = run_script(
            ROOT / "examples/centered-box/scpf/model.py"
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
        self.assertEqual(box["center"], [0, 0, 0])
        self.assertNotIn("corner", box)


if __name__ == "__main__":
    unittest.main()
