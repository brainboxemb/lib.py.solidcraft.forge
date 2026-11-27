import unittest

from scpf.core import Expression, Parameter
from scpf.ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
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


if __name__ == "__main__":
    unittest.main()
