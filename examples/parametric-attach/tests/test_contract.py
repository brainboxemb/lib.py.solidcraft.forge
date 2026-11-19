"""integration command contract for parametric-attach."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_parametric_attach_command_contract(self):
        rows = run_script(ROOT / "examples/parametric-attach/scpf/model.py")["commands"]
        parameter = next(row["params"] for row in rows if row["command"] == "parameters.add" and row["params"]["name"] == "gap")
        self.assertEqual(parameter["expression"], "10 mm")
        joint = next(row["params"] for row in rows if row["command"] == "joint.create")
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["b"]["occurrence"], "$block")
        self.assertEqual(joint["offset"], "gap")


if __name__ == "__main__":
    unittest.main()
