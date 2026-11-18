"""Q2 command contract for components."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_components_command_contract(self):
        rows = run_script(ROOT / "examples/components/scpf/model.py")["commands"]
        copies = [row["params"] for row in rows if row["command"] == "occurrence.copy"]
        self.assertEqual(copies, [{"component": "Block", "translate": [40.0, 0.0, 0.0]}])
        self.assertFalse(any(row["command"].startswith("joint.") for row in rows))
        self.assertFalse(any(row["command"] == "occurrence.move" for row in rows))


if __name__ == "__main__":
    unittest.main()
