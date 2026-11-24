"""Native SolidCraft exploded-view assembly contracts."""

import unittest

from scpf import Box, Placement, component
from scpf.assembly import compile_assembly
from scpf.model_objects import Assembly


@component
class ExplodedPanel:
    def build(self):
        return Box(20, 10, 2)


class ExplodedViewTests(unittest.TestCase):
    def make_three(self):
        first = ExplodedPanel()
        second = first.copy(placement=Placement(x=30))
        third = first.copy(placement=Placement(x=60))
        return first, second, third, first + second + third

    def test_automatic_view_is_created_after_real_occurrence_placements(self):
        _first, _second, _third, assembly = self.make_three()
        assembly = assembly.with_exploded_view(
            "Service",
            scale=1.5,
        ).show_exploded("Service")

        commands = compile_assembly(assembly, "Exploded")["commands"]
        create_index = next(
            i for i, row in enumerate(commands)
            if row["command"] == "explode.create"
        )
        placement_indices = [
            i for i, row in enumerate(commands)
            if row["command"] in ("occurrence.copy", "occurrence.move")
        ]
        self.assertTrue(placement_indices)
        self.assertLess(max(placement_indices), create_index)

        self.assertEqual(
            commands[create_index]["params"],
            {"name": "Service", "scale": 1.5},
        )
        self.assertEqual(
            commands[create_index + 1],
            {"command": "explode.show", "params": {"view": "Service"}},
        )

    def test_automatic_native_default_scale_is_omitted(self):
        _first, _second, _third, assembly = self.make_three()
        commands = compile_assembly(
            assembly.with_exploded_view("Default"),
            "Exploded",
        )["commands"]
        create = next(
            row for row in commands
            if row["command"] == "explode.create"
        )
        self.assertEqual(create["params"], {"name": "Default"})

    def test_explicit_moves_use_bound_occurrence_identity(self):
        _first, second, third, assembly = self.make_three()
        assembly = assembly.with_exploded_view(
            "Instructions",
            moves=[
                (second, (0, 25, 0)),
                (third, (0, 50, 10)),
            ],
        ).show_assembled()

        commands = compile_assembly(assembly, "Exploded")["commands"]
        create = next(
            row for row in commands
            if row["command"] == "explode.create"
        )
        self.assertEqual(create["params"]["name"], "Instructions")
        self.assertEqual(
            create["params"]["moves"],
            [
                {
                    "occurrence": "$explodedpanel_occurrence_2",
                    "translate": [0.0, 25.0, 0.0],
                },
                {
                    "occurrence": "$explodedpanel_occurrence_3",
                    "translate": [0.0, 50.0, 10.0],
                },
            ],
        )
        self.assertEqual(
            commands[-1],
            {"command": "explode.show", "params": {"view": None}},
        )

        copies = [
            row["params"] for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(
            copies,
            [
                {"component": "ExplodedPanel", "translate": [30.0, 0.0, 0.0]},
                {"component": "ExplodedPanel", "translate": [60.0, 0.0, 0.0]},
            ],
        )

    def test_view_validation_keeps_presentation_separate_from_composition(self):
        first, second, _third, assembly = self.make_three()
        outsider = ExplodedPanel()

        with self.assertRaisesRegex(ValueError, "either scale or explicit moves"):
            assembly.with_exploded_view(
                "Bad",
                scale=2,
                moves=[(second, (1, 0, 0))],
            )
        with self.assertRaisesRegex(ValueError, "belong to this assembly"):
            assembly.with_exploded_view(
                "Bad",
                moves=[(outsider, (1, 0, 0))],
            )
        with self.assertRaisesRegex(ValueError, "two moves"):
            assembly.with_exploded_view(
                "Bad",
                moves=[
                    (second, (1, 0, 0)),
                    (second, (2, 0, 0)),
                ],
            )
        with self.assertRaisesRegex(ValueError, "non-zero"):
            assembly.with_exploded_view(
                "Bad",
                moves=[(second, (0, 0, 0))],
            )
        with self.assertRaisesRegex(ValueError, "at least two"):
            Assembly((first,)).with_exploded_view("Bad")
        with self.assertRaisesRegex(ValueError, "compose the final assembly"):
            assembly.with_exploded_view("Ready") + outsider

    def test_show_requires_defined_view(self):
        _first, _second, _third, assembly = self.make_three()
        with self.assertRaises(KeyError):
            assembly.show_exploded("Missing")


if __name__ == "__main__":
    unittest.main()
