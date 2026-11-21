"""Verification contract for symbolic occurrence Placement."""
from pathlib import Path
import unittest
from scpf.runner import run_script
ROOT = Path(__file__).resolve().parents[3]
class ParametricMoveCommandTests(unittest.TestCase):
    def test_symbolic_move_uses_bound_occurrence_without_joint(self):
        commands = run_script(ROOT / "examples/parametric-move/scpf/model.py")["commands"]
        move = next(row["params"] for row in commands if row["command"] == "occurrence.move")
        self.assertTrue(move["occurrence"].startswith("$"))
        self.assertIn("offset", str(move["translate"][0]))
        self.assertFalse(any(row["command"].startswith("joint.") for row in commands))
if __name__ == "__main__":
    unittest.main()
