"""Qualification contract for native attachment angle."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class AttachAngleCommandTests(unittest.TestCase):
    def test_quarter_turn_is_emitted_on_rigid_joint(self):
        document = run_script(
            ROOT / "examples/attach-angle/scpf/model.py"
        )
        joints = [
            row["params"]
            for row in document["commands"]
            if row["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 1)
        self.assertEqual(joints[0]["type"], "rigid")
        self.assertEqual(joints[0]["angle"], 90)
        self.assertEqual(joints[0]["a"]["occurrence"], "$base")
        self.assertEqual(joints[0]["b"]["occurrence"], "$arm")


if __name__ == "__main__":
    unittest.main()
