"""Matrix tests for body and feature compatibility."""

import unittest

from scpf import Hole
from scpf.compiler import compile_model
from scpf.csg import CSG_PRIMITIVE_KINDS

from .geometry_contracts import (
    ALL_FEATURE_BODY_CASES,
    PRIMITIVE_BODY_CASES,
)


class GeometryCompatibilityContracts(unittest.TestCase):
    def test_primitive_registry_matches_compiler_support(self):
        registered = {case.kind for case in PRIMITIVE_BODY_CASES}
        self.assertEqual(registered, CSG_PRIMITIVE_KINDS)

    def test_every_registered_primitive_compiles_as_new_body(self):
        for case in PRIMITIVE_BODY_CASES:
            with self.subTest(body=case.name):
                commands = compile_model(case.build(), "Part")["commands"]
                native = [row for row in commands if row["command"].startswith("solid.")]
                self.assertEqual(len(native), 1)
                self.assertEqual(native[0]["params"]["operation"], "new")
                self.assertEqual(native[0]["params"]["body_name"], "Part")

    def test_explicit_hole_contract_runs_on_every_feature_body(self):
        for case in ALL_FEATURE_BODY_CASES:
            with self.subTest(body=case.name):
                body = case.build()
                hole = Hole(
                    d=6,
                    depth=case.hole_depth,
                    direction=(0, 0, -1),
                ).at(*case.hole_position)
                commands = compile_model(body + hole, "Part")["commands"]
                holes = [row for row in commands if row["command"] == "solid.hole"]
                self.assertEqual(len(holes), 1)
                self.assertEqual(holes[0]["params"]["diameter"], 6)
                self.assertEqual(holes[0]["params"]["targets"], ["Part"])

    def test_multiple_explicit_holes_work_on_every_feature_body(self):
        for case in ALL_FEATURE_BODY_CASES:
            with self.subTest(body=case.name):
                body = case.build()
                for x in (-5, 5):
                    body = body + Hole(
                        d=4,
                        depth=case.hole_depth,
                        direction=(0, 0, -1),
                    ).at(x, 0, case.hole_position[2])
                commands = compile_model(body, "Part")["commands"]
                holes = [row for row in commands if row["command"] == "solid.hole"]
                self.assertEqual(len(holes), 2)
                self.assertEqual(
                    [row["params"]["position"][0] for row in holes],
                    [-5, 5],
                )


if __name__ == "__main__":
    unittest.main()
