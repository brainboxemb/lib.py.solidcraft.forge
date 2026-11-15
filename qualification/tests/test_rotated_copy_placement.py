"""Command contract for a copied Placement with translation and rotation."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class RotatedCopyPlacementCommandTests(unittest.TestCase):
    def test_copy_stays_at_identity_until_complete_pose_is_applied(self):
        document = run_script(
            ROOT / "examples/rotated-copy-placement/scpf/model.py"
        )
        commands = document["commands"]

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
        self.assertEqual(
            moves,
            [{
                "occurrence": "Panel:2",
                "translate": [30.0, 0.0, 40.0],
                "axis": [1.0, 0.0, 0.0],
                "angle": "90 deg",
            }],
        )

        self.assertFalse(any(
            row["command"] == "joint.create"
            for row in commands
        ))


if __name__ == "__main__":
    unittest.main()
