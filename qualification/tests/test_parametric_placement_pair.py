"""Qualification contract for symmetric parametric occurrence Placement."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class ParametricPlacementPairCommandTests(unittest.TestCase):
    def test_symmetric_pair_keeps_one_parameter_and_two_expressed_placements(self):
        document = run_script(
            ROOT / "examples/parametric-placement-pair/scpf/model.py"
        )
        commands = document["commands"]

        parameters = [
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        ]
        self.assertEqual(
            [(row["name"], row["expression"]) for row in parameters],
            [("spacing", "80")],
        )

        creates = [
            row["params"]
            for row in commands
            if row["command"] == "component.create"
        ]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0]["name"], "Block")

        copies = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(copies, [{"component": "Block"}])

        moves = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.move"
        ]
        self.assertEqual(len(moves), 2)
        self.assertEqual(
            [row["translate"][0] for row in moves],
            ["-(spacing / 2)", "spacing / 2"],
        )
        self.assertFalse(any(
            row["command"] == "joint.create"
            for row in commands
        ))


if __name__ == "__main__":
    unittest.main()
