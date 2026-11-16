"""Qualification contract for reusable component definition identity."""

from dataclasses import dataclass
import unittest

from scpf.core import Axis, Box, Parameter
from scpf.assembly import compile_assembly
from scpf.runner import component


class DefinitionIdentityQualificationTests(unittest.TestCase):
    def test_local_names_are_unique_and_external_name_stays_shared(self):
        class Foo:
            width = 10.0

            def build(self):
                return Box(self.width, 10, 2)

        class Foo_2:
            width = 30.0

            def build(self):
                return Box(self.width, 10, 2)

        FooPart = component(Foo, include=("width",))
        Foo2Part = component(Foo_2, include=("width",))

        commands = compile_assembly(
            FooPart(width=10)
            + FooPart(width=20)
            + Foo2Part(width=30),
            "Display",
        )["commands"]
        names = [
            row["params"]["name"]
            for row in commands
            if row["command"] == "parameters.add"
        ]
        self.assertEqual(
            names,
            [
                "d1_Foo_width",
                "d2_Foo_2_width",
                "d3_Foo_2_width",
            ],
        )

        class Panel:
            width = 40.0

            def build(self):
                return Box(self.width, 10, 2)

        PanelPart = component(Panel)
        document = compile_assembly(
            PanelPart(width=Parameter("opening_width", 800)),
            "PanelDisplay",
        )
        shared_names = [
            row["params"]["name"]
            for row in document["commands"]
            if row["command"] == "parameters.add"
        ]
        self.assertEqual(shared_names, ["opening_width"])

    def test_fixed_dataclass_variants_have_different_definition_keys(self):
        @dataclass
        class Variant:
            enabled: object = True
            label: str = "wide"
            axis: Axis = Axis.X

            def build(self):
                return Box(
                    20 if self.enabled is True else 10,
                    30 if self.label == "wide" else 15,
                    8 if self.axis is Axis.X else 12,
                )

        Part = component(Variant)
        parts = [
            Part(),
            Part(enabled=False),
            Part(enabled=1),
            Part(label="narrow"),
            Part(axis=Axis.Y),
        ]
        self.assertEqual(
            len({part.definition.key for part in parts}),
            len(parts),
        )


if __name__ == "__main__":
    unittest.main()
