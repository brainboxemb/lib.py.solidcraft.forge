"""Qualification contract for parent-derived child dimensions."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class ParentDerivedChildSizeCommandTests(unittest.TestCase):
    def test_child_dimensions_keep_parent_expressions(self):
        document = run_script(
            ROOT / "examples/parent-derived-child-size/scpf/model.py"
        )
        commands = document["commands"]

        parameters = [
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        ]
        self.assertEqual(
            [(row["name"], row["expression"]) for row in parameters],
            [
                ("base_width", "120"),
                ("base_depth", "80"),
            ],
        )

        boxes = [
            row["params"]
            for row in commands
            if row["command"] == "solid.box"
        ]
        self.assertEqual(len(boxes), 2)

        dimensions = {
            (row["length"], row["width"], row["height"])
            for row in boxes
        }
        self.assertIn(("base_width", "base_depth", 10.0), dimensions)
        self.assertIn(
            ("base_width / 2", "base_depth / 2", 6.0),
            dimensions,
        )

        components = [
            row["params"]["name"]
            for row in commands
            if row["command"] == "component.create"
        ]
        self.assertEqual(components, ["ParentBlock", "DerivedChild"])


if __name__ == "__main__":
    unittest.main()
