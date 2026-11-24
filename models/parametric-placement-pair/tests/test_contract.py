"""Qualification contract for symmetric parametric Placement."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class ParametricPlacementPairCommandTests(unittest.TestCase):
    def test_symmetric_parametric_pair_uses_bound_occurrences(self):
        document = run_script(
            ROOT / "models/parametric-placement-pair/scpf/model.py"
        )
        commands = document["commands"]
        moves = [
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        ]

        self.assertEqual(len(moves), 2)
        self.assertEqual(
            {move["occurrence"] for move in moves},
            {"$block_occurrence_1", "$block_occurrence_2"},
        )
        self.assertTrue(all(
            "spacing" in str(move["translate"][0])
            for move in moves
        ))
        self.assertFalse(any(
            command["command"].startswith("joint.")
            for command in commands
        ))


if __name__ == "__main__":
    unittest.main()
