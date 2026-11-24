"""Command contract for native exploded assembly views."""

import json
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "models/exploded-views"
MODEL = EXAMPLE / "scpf/model.py"


class ExplodedViewsContractTests(unittest.TestCase):
    def setUp(self):
        self.commands = run_script(MODEL)["commands"]

    def test_normal_placements_precede_exploded_presentations(self):
        explode_index = next(
            i for i, row in enumerate(self.commands)
            if row["command"] == "explode.create"
        )
        placement_indices = [
            i for i, row in enumerate(self.commands)
            if row["command"] in ("occurrence.copy", "occurrence.move")
        ]
        self.assertEqual(len(placement_indices), 2)
        self.assertLess(max(placement_indices), explode_index)

    def test_automatic_and_explicit_views_lower_natively(self):
        creates = [
            row["params"] for row in self.commands
            if row["command"] == "explode.create"
        ]
        self.assertEqual(
            creates[0],
            {"name": "Automatic", "scale": 1.25},
        )
        self.assertEqual(creates[1]["name"], "Instructions")
        self.assertEqual(
            creates[1]["moves"],
            [
                {
                    "occurrence": "$explodeblock_occurrence_2",
                    "translate": [0.0, 25.0, 0.0],
                },
                {
                    "occurrence": "$explodeblock_occurrence_3",
                    "translate": [0.0, 50.0, 10.0],
                },
            ],
        )
        self.assertEqual(
            self.commands[-1],
            {"command": "explode.show", "params": {"view": None}},
        )

    def test_explosion_never_becomes_occurrence_move(self):
        self.assertFalse(any(
            row["command"] == "occurrence.move"
            for row in self.commands
        ))

    def test_saved_design_commands_address_persistent_views(self):
        automatic = json.loads(
            (EXAMPLE / "verification/show_automatic.json").read_text()
        )
        instructions = json.loads(
            (EXAMPLE / "verification/show_instructions_then_assembled.json")
            .read_text()
        )
        self.assertEqual(
            automatic["commands"],
            [{"command": "explode.show", "params": {"view": "Automatic"}}],
        )
        self.assertEqual(
            instructions["commands"][-1],
            {"command": "explode.show", "params": {"view": None}},
        )


if __name__ == "__main__":
    unittest.main()
