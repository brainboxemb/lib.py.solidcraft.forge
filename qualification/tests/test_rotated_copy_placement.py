"""Qualification contract for copied Placement with rotation."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class RotatedCopyPlacementCommandTests(unittest.TestCase):
    def test_copy_is_created_at_identity_then_receives_complete_pose(self):
        commands = run_script(
            ROOT / "examples/rotated-copy-placement/scpf/model.py"
        )["commands"]

        copies = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(copies, [{"component": "Panel"}])

        moves = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.move"
        ]
        self.assertEqual(len(moves), 2)
        self.assertEqual(
            [row["translate"] for row in moves],
            [[-40.0, 0.0, 0.0], [40.0, 0.0, 0.0]],
        )
        self.assertTrue(
            all(row["axis"] == [0.0, 0.0, 1.0] for row in moves)
        )
        self.assertTrue(all(row["angle"] == "90 deg" for row in moves))
        self.assertFalse(any(
            row["command"] == "joint.create"
            for row in commands
        ))


if __name__ == "__main__":
    unittest.main()
