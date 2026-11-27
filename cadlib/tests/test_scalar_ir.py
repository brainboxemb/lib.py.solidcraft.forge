import unittest

from scpf import cadmath
from scpf.core import Expression, Parameter
from scpf.ir import (
    ScalarBinaryIR,
    ScalarFunctionIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarPowerIR,
    ScalarUnaryIR,
)
from scpf.scalar_ir import (
    is_affine_scalar_expression,
    scalar_parameter_names,
)


class ScalarExpressionIRTests(unittest.TestCase):
    def test_parameter_add_literal_captures_semantic_tree(self):
        shared = Parameter("shared", 4)

        expression = shared + 1

        self.assertEqual(expression.expression, "shared + 1 mm")
        self.assertEqual(
            expression.scalar_ir,
            ScalarBinaryIR(
                "add",
                ScalarParameterRefIR("shared"),
                ScalarLiteralIR(1),
            ),
        )
        self.assertEqual(
            scalar_parameter_names(expression.scalar_ir),
            ("shared",),
        )
        self.assertTrue(is_affine_scalar_expression(expression.scalar_ir))

    def test_chained_affine_operations_preserve_tree_without_text_parsing(self):
        shared = Parameter("shared", 4)

        expression = -(((shared + 2) * 3 - 1) / 2)

        self.assertIsInstance(expression.scalar_ir, ScalarUnaryIR)
        self.assertTrue(is_affine_scalar_expression(expression.scalar_ir))
        self.assertEqual(
            scalar_parameter_names(expression.scalar_ir),
            ("shared",),
        )

    def test_existing_three_argument_expression_remains_compatible(self):
        shared = Parameter("shared", 4)

        expression = Expression(5, "external_formula", (shared,))

        self.assertIsNone(expression.scalar_ir)
        self.assertEqual(
            expression,
            Expression(5, "external_formula", (shared,)),
        )
        self.assertNotIn("scalar_ir", repr(expression))

    def test_parameter_multiply_parameter_is_not_affine_dimensional_subset(self):
        left = Parameter("left", 4)
        right = Parameter("right", 3)

        expression = left * right

        self.assertIsInstance(expression.scalar_ir, ScalarBinaryIR)
        self.assertFalse(is_affine_scalar_expression(expression.scalar_ir))

    def test_numeric_divide_parameter_is_not_affine_dimensional_subset(self):
        shared = Parameter("shared", 4)

        expression = 12 / shared

        self.assertIsInstance(expression.scalar_ir, ScalarBinaryIR)
        self.assertFalse(is_affine_scalar_expression(expression.scalar_ir))

    def test_fixed_power_captures_semantic_tree(self):
        shared = Parameter("shared", 4)

        expression = shared ** 2

        self.assertEqual(
            expression.scalar_ir,
            ScalarPowerIR(ScalarParameterRefIR("shared"), 2),
        )
        self.assertEqual(
            scalar_parameter_names(expression.scalar_ir),
            ("shared",),
        )
        self.assertFalse(is_affine_scalar_expression(expression.scalar_ir))

    def test_all_public_cadmath_functions_capture_semantic_tree(self):
        left = Parameter("left", 9)
        right = Parameter("right", 4)

        cases = (
            (cadmath.min(left, right, 2), "min", 3),
            (cadmath.max(left, right, 2), "max", 3),
            (cadmath.sqrt(left), "sqrt", 1),
            (cadmath.abs(-left), "abs", 1),
            (cadmath.round(left / 2), "round", 1),
            (cadmath.floor(left / 2), "floor", 1),
            (cadmath.atan(right / left), "atan", 1),
        )

        for expression, name, arity in cases:
            with self.subTest(name=name):
                self.assertIsInstance(expression.scalar_ir, ScalarFunctionIR)
                self.assertEqual(expression.scalar_ir.name, name)
                self.assertEqual(len(expression.scalar_ir.arguments), arity)
                self.assertFalse(
                    is_affine_scalar_expression(expression.scalar_ir)
                )

    def test_nested_function_and_arithmetic_preserve_dependencies(self):
        left = Parameter("left", 9)
        right = Parameter("right", 4)

        expression = cadmath.max(
            cadmath.sqrt(left) + right,
            (left ** 2) / 3,
        )

        self.assertIsInstance(expression.scalar_ir, ScalarFunctionIR)
        self.assertEqual(
            scalar_parameter_names(expression.scalar_ir),
            ("left", "right"),
        )

    def test_cadmath_does_not_invent_semantics_for_text_only_expression(self):
        shared = Parameter("shared", 4)
        external = Expression(5, "external_formula", (shared,))

        expression = cadmath.abs(external)

        self.assertIsNone(expression.scalar_ir)


if __name__ == "__main__":
    unittest.main()
