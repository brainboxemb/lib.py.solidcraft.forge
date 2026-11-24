"""Qualification contract for the five native SolidCraft 0.45 Slot creators."""
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/slot-family/scpf/model.py"


class SlotFamilyQualificationTests(unittest.TestCase):
    def test_slot_family_command_contract(self):
        document = run_script(MODEL)
        self.assertEqual(document["format"], "scpf-replay")
        self.assertEqual(document["version"], 2)
        commands = document["commands"]

        native = []
        dimensioned = []
        direct = []
        for command in commands:
            if command["command"].startswith("sketch.slot."):
                native.append(command["command"])
                direct.append(command)
            elif command["command"] == "sketch.draw.dimensioned":
                creator = command["params"]["command"]
                if creator.startswith("sketch.slot."):
                    native.append(creator)
                    dimensioned.append(command)

        self.assertEqual(
            native,
            [
                "sketch.slot.center_to_center",
                "sketch.slot.overall",
                "sketch.slot.center_point",
                "sketch.slot.arc_three_point",
                "sketch.slot.arc_center",
            ],
        )
        self.assertEqual(
            [row["params"]["command"] for row in dimensioned],
            [
                "sketch.slot.center_to_center",
                "sketch.slot.overall",
                "sketch.slot.center_point",
            ],
        )
        self.assertEqual(
            [row["command"] for row in direct],
            [
                "sketch.slot.arc_three_point",
                "sketch.slot.arc_center",
            ],
        )
        self.assertNotIn(
            "sketch.rectangle.rounded",
            [command["command"] for command in commands],
        )

        # SolidCraft direct Slot point fields remain numeric even when Forge
        # retains parameter intent for the straight Slot dimensions.
        point_keys = ("p0", "p1", "center", "end", "start", "through")
        native_params = [
            row["params"]["params"] for row in dimensioned
        ] + [row["params"] for row in direct]
        for params in native_params:
            for key in point_keys:
                if key not in params:
                    continue
                self.assertTrue(
                    all(isinstance(value, (int, float)) for value in params[key]),
                    (key, params[key]),
                )
            self.assertEqual(params["width"], "slot_width")

        # Straight Slots use the canonical 0.45 dimensioned-sketch contract.
        for row in dimensioned:
            self.assertIn("length", row["params"]["dimensions"])
            self.assertEqual(
                set(row["bind"].values()),
                {"centre_line", "middle"},
            )

        self.assertEqual(
            [
                row["params"]["mode"]
                for row in commands
                if row["command"] == "sketch.constraint.horizontal_vertical"
            ],
            ["horizontal", "horizontal", "horizontal"],
        )
        middle_dimensions = [
            row["params"]
            for row in commands
            if row["command"] == "sketch.dimension"
        ]
        self.assertEqual(len(middle_dimensions), 6)
        self.assertEqual(
            [row["type"] for row in middle_dimensions],
            ["horizontal", "vertical"] * 3,
        )
        self.assertTrue(
            all(
                "abs(" in str(row["value"])
                for row in middle_dimensions
                if row["type"] == "vertical"
            )
        )

        face_query = next(
            command for command in commands
            if command["command"] == "model.faces"
        )
        self.assertEqual(face_query["params"], {"body": "SlotFamily"})
        create = next(
            command for command in commands
            if command["command"] == "sketch.create"
        )
        self.assertEqual(
            create["params"]["plane"],
            {
                "face": "$face_point_1",
                "body": "SlotFamily",
                "index": "$face_index_1",
            },
        )
        self.assertFalse(create["params"]["project_edges"])
        self.assertNotIn("offset", create["params"])

        box = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.box"
        )
        self.assertEqual(box["length"], "width")
        self.assertEqual(box["width"], "depth")
        self.assertEqual(box["height"], "thickness")

        extrude = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.extrude"
        )
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")
        self.assertEqual(extrude["operation"], "cut")
        self.assertNotIn("distance", extrude)


if __name__ == "__main__":
    unittest.main()
