"""Qualification contract for assembly-owned named anchors."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class AssemblyOwnedAnchorCommandTests(unittest.TestCase):
    def test_named_assembly_anchor_resolves_to_native_corner_relationship(self):
        document = run_script(
            ROOT / "examples/assembly-owned-anchor/scpf/model.py"
        )
        commands = document["commands"]

        parameters = [
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        ]
        self.assertEqual(
            [(row["name"], row["expression"]) for row in parameters],
            [
                ("base_width", "40"),
                ("base_height", "20"),
            ],
        )

        creates = [
            row["params"]["name"]
            for row in commands
            if row["command"] == "component.create"
        ]
        self.assertEqual(creates, ["Base", "Companion", "Marker"])

        joints = [
            row["params"]
            for row in commands
            if row["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 1)
        joint = joints[0]
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(
            joint["a"]["corner"],
            [20.0, -15.0, 20.0],
        )
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["b"]["occurrence"], "$marker")


if __name__ == "__main__":
    unittest.main()
