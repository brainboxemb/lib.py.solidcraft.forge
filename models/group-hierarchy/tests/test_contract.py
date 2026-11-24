"""Qualification contract for named native groups."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class GroupHierarchyCommandTests(unittest.TestCase):
    def test_group_lowers_to_real_nested_component(self):
        commands = run_script(
            ROOT / "models/group-hierarchy/scpf/model.py"
        )["commands"]

        created = [
            row["params"]
            for row in commands
            if row["command"] == "component.create"
        ]
        self.assertEqual(
            [row["name"] for row in created],
            ["PanelGroup", "Panel", "Frame"],
        )
        self.assertEqual(created[0]["activate"], False)
        self.assertFalse(created[0]["grounded"])
        self.assertEqual(created[1]["parent"], "PanelGroup")
        self.assertTrue(created[1]["grounded"])
        self.assertNotIn("parent", created[2])

        copies = [
            row["params"]["component"]
            for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(copies, ["Panel"])


if __name__ == "__main__":
    unittest.main()
