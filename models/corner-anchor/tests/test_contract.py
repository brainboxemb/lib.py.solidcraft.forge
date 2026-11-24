"""integration command contract for corner-anchor."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_corner_anchor_command_contract(self):
        rows = run_script(ROOT / "models/corner-anchor/scpf/model.py")["commands"]
        joint = next(row["params"] for row in rows if row["command"] == "joint.create")
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["a"]["corner"], [20.0, -15.0, 20.0])
        self.assertEqual(joint["b"]["occurrence"], "$marker")
        self.assertEqual(joint["b"]["point"], [20.0, -15.0, 20.0])


if __name__ == "__main__":
    unittest.main()
