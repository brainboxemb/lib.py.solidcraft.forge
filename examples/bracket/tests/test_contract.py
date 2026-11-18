"""Q2 command contract for bracket."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_bracket_command_contract(self):
        rows = run_script(ROOT / "examples/bracket/scpf/model.py")["commands"]
        sketch = next(row["params"] for row in rows if row["command"] == "sketch.create")
        polygon = next(row["params"] for row in rows if row["command"] == "sketch.line")
        extrude = next(row["params"] for row in rows if row["command"] == "solid.extrude")
        self.assertEqual(sketch, {"plane": "XZ", "name": "Profile"})
        self.assertTrue(polygon["closed"])
        self.assertEqual(len(polygon["points"]), 6)
        self.assertEqual(extrude["distance"], "width")
        self.assertEqual(extrude["direction"], "symmetric")


if __name__ == "__main__":
    unittest.main()
