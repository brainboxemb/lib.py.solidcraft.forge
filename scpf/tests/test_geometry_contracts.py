"""Reusable body × feature contract tests."""

import unittest

from scpf import Hole
from scpf.compiler import compile_model
from scpf.csg import CSG_PRIMITIVE_KINDS

from .geometry_contracts import (
    NATIVE_HOLE,
    PRIMITIVE_BODY_CASES,
    build_joined,
    cases_with,
)


class GeometryContractMatrix(unittest.TestCase):
    def test_primitive_registry_covers_every_compiler_primitive(self):
        self.assertEqual(
            {case.kind for case in PRIMITIVE_BODY_CASES},
            CSG_PRIMITIVE_KINDS,
        )

    def test_every_registered_primitive_compiles_as_a_new_body(self):
        for case in PRIMITIVE_BODY_CASES:
            with self.subTest(body=case.name):
                commands = compile_model(case.build(), "Part")["commands"]
                body_commands = [
                    row for row in commands
                    if row["command"] in {
                        "solid.box", "solid.cylinder", "solid.sphere"
                    }
                ]
                self.assertEqual(len(body_commands), 1)
                self.assertEqual(body_commands[0]["params"]["operation"], "new")
                self.assertEqual(body_commands[0]["params"]["body_name"], "Part")

    def test_native_hole_contract_runs_on_every_compatible_body(self):
        for case in cases_with(NATIVE_HOLE):
            with self.subTest(body=case.name):
                body = case.build()
                body = body + Hole(
                    d=6,
                    depth=case.through_depth,
                    direction=(0, 0, -1),
                ).at(0, 0, case.entry_z)

                commands = compile_model(body, "Part")["commands"]
                holes = [
                    row for row in commands
                    if row["command"] == "solid.hole"
                ]
                self.assertEqual(len(holes), 1)
                self.assertEqual(holes[0]["params"]["diameter"], 6)
                self.assertEqual(holes[0]["params"]["targets"], ["Part"])

    def test_native_hole_contract_survives_a_prior_join(self):
        for case in cases_with(NATIVE_HOLE):
            with self.subTest(body=case.name):
                body = build_joined(case)
                body = body + Hole(
                    d=6,
                    depth=case.through_depth,
                    direction=(0, 0, -1),
                ).at(0, 0, case.entry_z)

                commands = compile_model(body, "Part")["commands"]
                self.assertEqual(
                    [row["command"] for row in commands].count("solid.hole"),
                    1,
                )

    def test_native_hole_contract_supports_sequential_features(self):
        for case in cases_with(NATIVE_HOLE):
            with self.subTest(body=case.name):
                body = case.build()
                for x in (-5, 5):
                    body = body + Hole(
                        d=4,
                        depth=case.through_depth,
                        direction=(0, 0, -1),
                    ).at(x, 0, case.entry_z)

                commands = compile_model(body, "Part")["commands"]
                holes = [
                    row["params"] for row in commands
                    if row["command"] == "solid.hole"
                ]
                self.assertEqual(len(holes), 2)
                self.assertEqual(
                    [row["position"][0] for row in holes],
                    [-5, 5],
                )


if __name__ == "__main__":
    unittest.main()
