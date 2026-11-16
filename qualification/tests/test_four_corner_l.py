"""Qualification tests for four vertical L-profiles on rounded side corners."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class FourCornerLCommandTests(unittest.TestCase):
    def test_parametric_profile_placement_uses_replay_variables(self):
        commands = run_script(
            ROOT / "examples/four-corner-l/scpf/model.py"
        )["commands"]
        copies = [
            command for command in commands
            if command["command"] == "occurrence.copy"
        ]
        moves = [
            command["params"] for command in commands
            if command["command"] == "occurrence.move"
        ]
        self.assertEqual(len(copies), 3)
        self.assertEqual(len(moves), 4)
        self.assertTrue(all(
            move["occurrence"].startswith("$lprofile_occurrence_")
            for move in moves
        ))
        self.assertTrue(all(
            any(name in str(move["translate"])
                for name in ("frame_width", "frame_depth", "frame_height"))
            for move in moves
        ))
        self.assertFalse(any(
            command["command"].startswith("joint.")
            for command in commands
        ))


if __name__ == "__main__":
    unittest.main()
