"""Qualification contract for named native groups."""

import json
import os
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
NATIVE_ROOT = os.environ.get("SCPF_NATIVE_ROOT")


class GroupHierarchyCommandTests(unittest.TestCase):
    def test_group_lowers_to_real_nested_component(self):
        commands = run_script(
            ROOT / "examples/group-hierarchy/scpf/model.py"
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


@unittest.skipUnless(NATIVE_ROOT, "native SolidCraft evidence not supplied")
class GroupHierarchyNativeTests(unittest.TestCase):
    def test_group_geometry_survives_native_build(self):
        case = Path(NATIVE_ROOT) / "group-hierarchy"
        data = json.loads(
            (case / "measurements.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["body_count"], 3)

        inspection = json.loads(
            (case / "results-bom.json").read_text(encoding="utf-8")
        )
        components = inspection[2]["components"]
        by_name = {component["name"]: component for component in components}

        group = by_name["PanelGroup"]
        panel = by_name["Panel"]
        self.assertEqual(len(group["occurrences"]), 1)
        self.assertFalse(group["occurrences"][0]["grounded"])
        self.assertEqual(len(panel["occurrences"]), 2)
        self.assertTrue(panel["occurrences"][0]["grounded"])


if __name__ == "__main__":
    unittest.main()
