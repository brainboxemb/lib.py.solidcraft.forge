"""Qualification contract for eight trihedral flightcase corners."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class EightFlightcaseCornersCommandTests(unittest.TestCase):
    def test_parametric_corner_placement_uses_replay_variables(self):
        commands = run_script(
            ROOT / "examples/eight-flightcase-corners/scpf/model.py"
        )["commands"]
        copies = [
            command for command in commands
            if command["command"] == "occurrence.copy"
        ]
        moves = [
            command["params"] for command in commands
            if command["command"] == "occurrence.move"
        ]
        self.assertEqual(len(copies), 7)
        self.assertEqual(len(moves), 8)
        self.assertTrue(all(
            move["occurrence"].startswith("$flightcasecorner_occurrence_")
            for move in moves
        ))
        self.assertTrue(any(
            "case_height" in str(move["translate"])
            for move in moves
        ))
        self.assertFalse(any(
            command["command"].startswith("joint.")
            for command in commands
        ))


if __name__ == "__main__":
    unittest.main()
