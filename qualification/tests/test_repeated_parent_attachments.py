"""Command contract for repeated parent occurrences with attachments."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class RepeatedParentAttachmentCommandTests(unittest.TestCase):
    def test_two_authored_rigid_joints_use_bound_occurrences(self):
        commands = run_script(
            ROOT / "examples/repeated-parent-attachments/scpf/model.py"
        )["commands"]

        parameter = next(
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
            and row["params"]["name"] == "parent_height"
        )
        self.assertEqual((parameter["expression"], parameter["unit"]), ("40", "mm"))

        copies = [
            row
            for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(len(copies), 2)
        parent_copy = next(
            row for row in copies
            if row["params"]["component"] == "Parent"
        )
        self.assertEqual(parent_copy["params"]["translate"], [60, 0, 0])

        joints = [
            row["params"]
            for row in commands
            if row["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 2)
        self.assertTrue(all(row["type"] == "rigid" for row in joints))
        self.assertEqual(
            [row["a"]["occurrence"] for row in joints],
            ["$parent_occurrence_1", "$parent_occurrence_2"],
        )
        self.assertEqual(
            [row["a"]["face"] for row in joints],
            [[0.0, 0.0, 40.0], [60.0, 0.0, 40.0]],
        )
        self.assertEqual(
            [row["b"]["occurrence"] for row in joints],
            ["$marker_occurrence_1", "$marker_occurrence_2"],
        )
        self.assertEqual(
            [row["b"]["face"] for row in joints],
            [[0.0, 0.0, 40.0], [60.0, 0.0, 40.0]],
        )

        seed_moves = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.move"
        ]
        self.assertEqual(
            [row["occurrence"] for row in seed_moves],
            ["$marker_occurrence_1", "$marker_occurrence_2"],
        )
        self.assertEqual(
            [row["translate"] for row in seed_moves],
            [
                [0, 0, "parent_height"],
                [60.0, 0, "parent_height"],
            ],
        )
        self.assertFalse(any(
            "Place " in str(row.get("params", {}).get("name", ""))
            for row in commands
            if row["command"].startswith("joint.")
        ))


if __name__ == "__main__":
    unittest.main()
