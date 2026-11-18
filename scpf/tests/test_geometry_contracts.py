"""Reusable body × operation and body × feature contract tests."""

import unittest

from scpf import Anchor, Hole, Parameter
from scpf.compiler import compile_model
from scpf.csg import CSG_PRIMITIVE_KINDS

from geometry_contracts import (
    CSG,
    FEATURE_CASES,
    NATIVE_HOLE,
    PRIMITIVE_BODY_CASES,
    cases_with,
)


def _commands(document, name):
    return [
        row for row in document["commands"]
        if row["command"] == name
    ]


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
                native = _commands({"commands": commands}, case.native_command)
                self.assertEqual(len(native), 1)
                self.assertEqual(native[0]["params"]["operation"], "new")
                self.assertEqual(native[0]["params"]["body_name"], "Part")

    def test_every_registered_primitive_supports_bottom_at_placement(self):
        for case in PRIMITIVE_BODY_CASES:
            with self.subTest(body=case.name):
                placed = case.build().at(5, 6, 7, anchor=Anchor.BOTTOM)
                commands = compile_model(placed, "Part")["commands"]
                native = _commands(
                    {"commands": commands},
                    case.native_command,
                )[0]
                key, expected = case.bottom_at_expected
                self.assertEqual(
                    native["params"][key],
                    list(expected),
                )

    def test_every_registered_primitive_preserves_parameters(self):
        for case in PRIMITIVE_BODY_CASES:
            with self.subTest(body=case.name):
                size = Parameter("size", 30)
                body = case.build_parameterized(size)
                commands = compile_model(body, "Part")["commands"]

                parameters = _commands(
                    {"commands": commands}, "parameters.add"
                )
                self.assertEqual(
                    [row["params"]["name"] for row in parameters],
                    ["size"],
                )
                primitive = _commands(
                    {"commands": commands}, case.native_command
                )[0]
                self.assertIn("size", str(primitive["params"]))

    def test_csg_operations_cover_every_primitive_pair(self):
        operations = (
            ("join", lambda left, right: left + right),
            ("cut", lambda left, right: left - right),
            ("intersect", lambda left, right: left & right),
        )
        csg_cases = cases_with(CSG)

        for operation, combine in operations:
            for left_case in csg_cases:
                for right_case in csg_cases:
                    with self.subTest(
                        operation=operation,
                        left=left_case.name,
                        right=right_case.name,
                    ):
                        result = combine(
                            left_case.build(),
                            right_case.build().move(x=5),
                        )
                        commands = compile_model(result, "Part")["commands"]

                        self.assertEqual(
                            commands[0]["params"]["operation"],
                            "new",
                        )
                        self.assertEqual(
                            commands[-1]["params"]["operation"],
                            operation,
                        )
                        self.assertEqual(
                            commands[-1]["params"]["targets"],
                            ["Part"],
                        )

    def test_every_feature_contract_runs_on_every_compatible_body(self):
        for feature in FEATURE_CASES:
            for case in cases_with(feature.capability):
                with self.subTest(feature=feature.name, body=case.name):
                    body = feature.apply(case.build(), case)
                    document = compile_model(body, "Part")
                    native = _commands(document, feature.native_command)
                    self.assertEqual(len(native), feature.expected_count)
                    self.assertTrue(
                        all(row["params"].get("targets") == ["Part"] for row in native)
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

                holes = _commands(
                    compile_model(body, "Part"),
                    "solid.hole",
                )
                self.assertEqual(len(holes), 2)
                self.assertEqual(
                    [row["params"]["position"][0] for row in holes],
                    [-5, 5],
                )


if __name__ == "__main__":
    unittest.main()
