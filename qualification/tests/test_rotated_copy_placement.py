"""Qualification guard for replayable copied Placement rotation."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class RotatedCopyPlacementCommandTests(unittest.TestCase):
    def test_rotated_copy_binds_occurrence_before_move(self):
        document = run_script(
            ROOT / "examples/rotated-copy-placement/scpf/model.py"
        )
        commands = document["commands"]
        copy = next(
            command
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )

        variable = next(iter(copy["bind"]))
        self.assertTrue(variable.startswith("$"))
        self.assertEqual(copy["bind"][variable], "occurrence")
        self.assertEqual(move["occurrence"], variable)
        self.assertIn("axis", move)
        self.assertIn("angle", move)
        self.assertFalse(any(
            ":2" in str(command["params"])
            for command in commands
        ))


if __name__ == "__main__":
    unittest.main()
