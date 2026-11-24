"""Command-contract checks for Cone Boolean feature compilation."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[1]


class ConeBooleanContractTests(unittest.TestCase):
    def test_placed_cone_joins_existing_featured_body_natively(self):
        commands = run_script(ROOT / "scpf" / "model.py")["commands"]
        cone = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.cone"
        )
        self.assertEqual(cone["operation"], "join")
        self.assertEqual(cone["targets"], ["ConeBoolean"])
        self.assertEqual(cone["base"], [0, 0, 18])
        self.assertEqual(cone["diameter"], 18)
        self.assertEqual(cone["top_diameter"], 10)
        self.assertEqual(cone["height"], 8)


if __name__ == "__main__":
    unittest.main()
