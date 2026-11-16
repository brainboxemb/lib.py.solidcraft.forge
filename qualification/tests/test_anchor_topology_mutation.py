"""Qualification contract for native AnchorTopology mutation."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class AnchorTopologyMutationCommandTests(unittest.TestCase):
    def test_fixed_topology_pick_is_inlined(self):
        document = run_script(
            ROOT / "examples/anchor-topology-mutation/scpf/model.py"
        )
        commands = document["commands"]

        self.assertFalse(
            any(row["command"] == "joint.origin" for row in commands)
        )

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

        joint = next(
            row["params"]
            for row in commands
            if row["command"] == "joint.create"
        )
        self.assertEqual(
            joint["a"],
            {
                "occurrence": "$board",
                "edge": [-20.0, -10.0, 10.0],
                "on": [0.0, -10.0, 10.0],
                "corner": [-20.0, -10.0, 20.0],
                "z": [0.0, -1.0, 0.0],
                "x": [0.0, 0.0, -1.0],
            },
        )
        self.assertEqual(joint["b"]["occurrence"], "$marker")
        # The first Marker occurrence is created at native identity. The
        # joint owns the relationship, so its child frame stays local here.
        self.assertEqual(joint["b"]["point"], [0.0, 0.0, 0.0])
        self.assertEqual(joint["b"]["z"], [0.0, 0.0, 1.0])
        self.assertEqual(joint["b"]["x"], [1.0, 0.0, 0.0])
        self.assertEqual(joint["angle"], 0.0)


if __name__ == "__main__":
    unittest.main()
