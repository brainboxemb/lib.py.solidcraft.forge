"""Qualification contract for prepositioned as-built attachment."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class AsBuiltAttachCommandTests(unittest.TestCase):
    def test_prepositioned_as_built_occurrence_uses_bound_id(self):
        document = run_script(
            ROOT / "examples/as-built-attach/scpf/model.py"
        )
        commands = document["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
            and command["params"]["occurrence"].startswith("$marker")
        )
        self.assertEqual(move["translate"], [50, 20, 15])
        self.assertEqual(move["axis"], [0.0, 0.0, 1.0])
        self.assertEqual(move["angle"], "90 deg")

        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.as_built"
        )
        self.assertEqual(joint["a"], "$base")
        self.assertEqual(joint["b"], "$marker")


if __name__ == "__main__":
    unittest.main()
