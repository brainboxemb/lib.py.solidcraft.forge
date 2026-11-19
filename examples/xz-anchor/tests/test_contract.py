"""integration command contract for xz-anchor."""

from pathlib import Path
import unittest
from scpf.runner import run_script

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTests(unittest.TestCase):
    def test_xz_anchor_command_contract(self):
        rows = run_script(ROOT / "examples/xz-anchor/scpf/model.py")["commands"]
        sketch = next(row["params"] for row in rows if row["command"] == "sketch.create")
        self.assertEqual(sketch, {"plane": "XZ", "name": "Profile"})
        joints = [row["params"] for row in rows if row["command"] == "joint.create"]
        self.assertEqual(len(joints), 2)
        self.assertEqual([joint["a"]["corner"] for joint in joints], [[20.0, 0.0, 20.0], [-20.0, 0.0, 20.0]])
        self.assertEqual([joint["b"]["occurrence"] for joint in joints], ["$rightmarker", "$leftmarker"])


if __name__ == "__main__":
    unittest.main()
