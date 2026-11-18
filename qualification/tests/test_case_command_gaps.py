"""Focused Q2 command contracts for cases without a dedicated module."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


def commands(slug: str) -> list[dict]:
    return run_script(
        ROOT / "examples" / slug / "scpf" / "model.py"
    )["commands"]


class MissingCaseCommandContractTests(unittest.TestCase):
    def test_anchored_holes_command_contract(self):
        rows = commands("anchored-holes")

        self.assertEqual(
            [
                row["params"]["name"]
                for row in rows
                if row["command"] == "sketch.create"
            ],
            ["Base", "Hole"],
        )

        circles = [
            row["params"]
            for row in rows
            if row["command"] == "sketch.circle.center"
        ]
        self.assertEqual(len(circles), 1)
        self.assertEqual(circles[0]["diameter"], 8)
        self.assertEqual(
            circles[0]["center"],
            ["(width / 2)", "((depth - spacing) / 2)"],
        )

        cuts = [
            row["params"]
            for row in rows
            if row["command"] == "solid.extrude"
            and row["params"].get("operation") == "cut"
        ]
        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0]["name"], "Hole")

        patterns = [
            row["params"]
            for row in rows
            if row["command"] == "solid.pattern.rectangular"
        ]
        self.assertEqual(len(patterns), 1)
        self.assertEqual(
            patterns[0],
            {
                "features": ["Hole"],
                "dir1": [0.0, 1.0, 0.0],
                "count1": 2,
                "spacing1": "spacing",
                "alignment": "right",
                "reversed": False,
            },
        )

    def test_components_command_contract(self):
        rows = commands("components")
        copies = [
            row["params"]
            for row in rows
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(
            copies,
            [{"component": "Block", "translate": [40.0, 0.0, 0.0]}],
        )
        self.assertFalse(
            any(row["command"].startswith("joint.") for row in rows)
        )
        self.assertFalse(
            any(row["command"] == "occurrence.move" for row in rows)
        )

    def test_parametric_attach_command_contract(self):
        rows = commands("parametric-attach")
        parameter = next(
            row["params"]
            for row in rows
            if row["command"] == "parameters.add"
            and row["params"]["name"] == "gap"
        )
        self.assertEqual(parameter["expression"], "10 mm")

        joint = next(
            row["params"]
            for row in rows
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["b"]["occurrence"], "$block")
        self.assertEqual(joint["offset"], "gap")

    def test_parametric_offset_command_contract(self):
        rows = commands("parametric-offset")
        parameter = next(
            row["params"]
            for row in rows
            if row["command"] == "parameters.add"
            and row["params"]["name"] == "shift"
        )
        self.assertEqual(parameter["expression"], "5 mm")

        joint = next(
            row["params"]
            for row in rows
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "planar")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["b"]["occurrence"], "$marker")
        self.assertEqual(joint["values"], [0, "-(shift)", 0.0])

    def test_parametric_anchor_command_contract(self):
        rows = commands("parametric-anchor")
        parameter = next(
            row["params"]
            for row in rows
            if row["command"] == "parameters.add"
            and row["params"]["name"] == "base_width"
        )
        self.assertEqual(
            (parameter["expression"], parameter["unit"]),
            ("40", "mm"),
        )

        box = next(
            row["params"]
            for row in rows
            if row["command"] == "solid.box"
            and row["params"]["body_name"] == "Base"
        )
        self.assertEqual(box["length"], "base_width")

        joint = next(
            row["params"]
            for row in rows
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(
            joint["a"],
            {"face": [20.0, 0.0, 5.0], "occurrence": "$base"},
        )
        self.assertEqual(
            joint["b"],
            {"face": [20.0, 0.0, 5.0], "occurrence": "$block"},
        )

    def test_corner_anchor_command_contract(self):
        joint = next(
            row["params"]
            for row in commands("corner-anchor")
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["a"]["occurrence"], "$base")
        self.assertEqual(joint["a"]["corner"], [20.0, -15.0, 20.0])
        self.assertEqual(joint["b"]["occurrence"], "$marker")
        self.assertEqual(joint["b"]["point"], [20.0, -15.0, 20.0])

    def test_xz_anchor_command_contract(self):
        rows = commands("xz-anchor")
        sketch = next(
            row["params"]
            for row in rows
            if row["command"] == "sketch.create"
        )
        self.assertEqual(
            sketch,
            {"plane": "XZ", "name": "Profile"},
        )

        joints = [
            row["params"]
            for row in rows
            if row["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 2)
        self.assertEqual(
            [joint["a"]["corner"] for joint in joints],
            [[20.0, 0.0, 20.0], [-20.0, 0.0, 20.0]],
        )
        self.assertEqual(
            [joint["b"]["occurrence"] for joint in joints],
            ["$rightmarker", "$leftmarker"],
        )

    def test_bracket_command_contract(self):
        rows = commands("bracket")
        sketch = next(
            row["params"]
            for row in rows
            if row["command"] == "sketch.create"
        )
        polygon = next(
            row["params"]
            for row in rows
            if row["command"] == "sketch.line"
        )
        extrude = next(
            row["params"]
            for row in rows
            if row["command"] == "solid.extrude"
        )

        self.assertEqual(
            sketch,
            {"plane": "XZ", "name": "Profile"},
        )
        self.assertTrue(polygon["closed"])
        self.assertEqual(len(polygon["points"]), 6)
        self.assertEqual(extrude["distance"], "width")
        self.assertEqual(extrude["direction"], "symmetric")


if __name__ == "__main__":
    unittest.main()
