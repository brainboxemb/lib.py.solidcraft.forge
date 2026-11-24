"""integration command contract for parametric-offset."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_parametric_offset_command_contract(self):
        rows = run_script(ROOT / "models/parametric-offset/scpf/model.py")["commands"]
        parameter = next(row["params"] for row in rows if row["command"] == "parameters.add" and row["params"]["name"] == "shift")
        self.assertEqual(parameter["expression"], "5 mm")
        joint = next(row["params"] for row in rows if row["command"] == "joint.create")
        self.assertEqual(joint["type"], "planar")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["b"]["occurrence"], "$marker")
        self.assertEqual(joint["values"], [0, "-(shift)", 0.0])


if __name__ == "__main__":
    unittest.main()
