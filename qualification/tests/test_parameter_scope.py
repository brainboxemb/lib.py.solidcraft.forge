"""Qualification tests for change 0003: explicit child publication and inherited bindings."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class ParameterScopeCommandTests(unittest.TestCase):
    def test_generated_parameter_contract(self):
        document = run_script(
            ROOT / "examples/parameter-scope/scpf/model.py"
        )

        params = _parameter_commands(document)
        self.assertEqual(
            [(row["name"], row["expression"]) for row in params],
            [
                ("d1_Panel_width", "40"),
                ("d2_Panel_2_width", "60"),
                ("shared_width", "80"),
            ],
        )

        boxes = [
            row["params"]
            for row in document["commands"]
            if row["command"] == "solid.box"
        ]
        self.assertEqual(len(boxes), 4)

        lengths = [row["length"] for row in boxes]
        self.assertIn("d1_Panel_width", lengths)
        self.assertIn("d2_Panel_2_width", lengths)
        self.assertIn("shared_width", lengths)
        self.assertIn("shared_width / 2", lengths)

        self.assertFalse(any(
            row["name"].startswith(("d1_Panel", "d2_Panel")) and row["name"].endswith("_depth")
            for row in params
        ))
        self.assertTrue(all(row["width"] == 20.0 for row in boxes))

        creates = [
            row["params"]["name"]
            for row in document["commands"]
            if row["command"] == "component.create"
        ]
        self.assertEqual(creates, ["Panel", "Panel 2", "Panel 3", "Panel 4"])

        copies = [
            row for row in document["commands"]
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(len(copies), 1)


if __name__ == "__main__":
    unittest.main()
