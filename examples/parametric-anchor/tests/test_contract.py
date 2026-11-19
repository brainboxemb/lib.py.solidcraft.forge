"""integration command contract for parametric-anchor."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_parametric_anchor_command_contract(self):
        rows = run_script(ROOT / "examples/parametric-anchor/scpf/model.py")["commands"]
        parameter = next(row["params"] for row in rows if row["command"] == "parameters.add" and row["params"]["name"] == "base_width")
        self.assertEqual((parameter["expression"], parameter["unit"]), ("40", "mm"))
        box = next(row["params"] for row in rows if row["command"] == "solid.box" and row["params"]["body_name"] == "Base")
        self.assertEqual(box["length"], "base_width")
        joint = next(row["params"] for row in rows if row["command"] == "joint.create")
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["a"], {"face": [20.0, 0.0, 5.0], "occurrence": "$base"})
        self.assertEqual(joint["b"], {"face": [20.0, 0.0, 5.0], "occurrence": "$block"})


if __name__ == "__main__":
    unittest.main()
