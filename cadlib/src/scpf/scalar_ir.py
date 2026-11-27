"""Engine-neutral scalar arithmetic used by Forge semantic CAD values.

The public authoring layer keeps its existing human/native-oriented expression
text for compatibility. These immutable nodes preserve the arithmetic meaning
separately so typed CAD use sites can apply length/angle semantics without
parsing that text.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ScalarLiteralIR:
    """One finite authored numeric literal without an intrinsic physical unit."""

    value: float

    def __post_init__(self):
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not isfinite(self.value)
        ):
            raise ValueError("ScalarLiteralIR value must be finite numeric")


@dataclass(frozen=True)
class ScalarParameterRefIR:
    """Reference one declared Forge parameter by semantic name."""

    name: str

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.isidentifier():
            raise ValueError(
                "ScalarParameterRefIR name must be a valid identifier"
            )


@dataclass(frozen=True)
class ScalarUnaryIR:
    """One unary scalar arithmetic operation."""

    operation: str
    operand: "ScalarExpressionIR"

    def __post_init__(self):
        if self.operation != "negate":
            raise ValueError("ScalarUnaryIR currently supports negate only")
        if not _is_scalar_expression(self.operand):
            raise ValueError("ScalarUnaryIR operand must be scalar expression IR")


@dataclass(frozen=True)
class ScalarPowerIR:
    """One scalar value raised to a fixed finite numeric exponent."""

    base: "ScalarExpressionIR"
    exponent: float

    def __post_init__(self):
        if not _is_scalar_expression(self.base):
            raise ValueError("ScalarPowerIR base must be scalar expression IR")
        if (
            isinstance(self.exponent, bool)
            or not isinstance(self.exponent, (int, float))
            or not isfinite(self.exponent)
        ):
            raise ValueError("ScalarPowerIR exponent must be finite numeric")


@dataclass(frozen=True)
class ScalarFunctionIR:
    """One public symbolic CAD-math function over scalar expression IR."""

    name: str
    arguments: tuple["ScalarExpressionIR", ...]

    def __post_init__(self):
        arity = {
            "sqrt": 1,
            "abs": 1,
            "round": 1,
            "floor": 1,
            "atan": 1,
        }
        if self.name in {"min", "max"}:
            if len(self.arguments) < 2:
                raise ValueError(
                    f"ScalarFunctionIR {self.name} requires at least two arguments"
                )
        elif self.name in arity:
            if len(self.arguments) != arity[self.name]:
                raise ValueError(
                    f"ScalarFunctionIR {self.name} requires one argument"
                )
        else:
            raise ValueError("ScalarFunctionIR function is unsupported")
        if any(not _is_scalar_expression(value) for value in self.arguments):
            raise ValueError(
                "ScalarFunctionIR arguments must be scalar expression IR"
            )


@dataclass(frozen=True)
class ScalarBinaryIR:
    """One binary scalar arithmetic operation."""

    operation: str
    left: "ScalarExpressionIR"
    right: "ScalarExpressionIR"

    def __post_init__(self):
        if self.operation not in {"add", "subtract", "multiply", "divide"}:
            raise ValueError(
                "ScalarBinaryIR operation must be add/subtract/multiply/divide"
            )
        if (
            not _is_scalar_expression(self.left)
            or not _is_scalar_expression(self.right)
        ):
            raise ValueError(
                "ScalarBinaryIR operands must be scalar expression IR"
            )
        if (
            self.operation == "divide"
            and isinstance(self.right, ScalarLiteralIR)
            and self.right.value == 0
        ):
            raise ValueError("ScalarBinaryIR cannot divide by zero")


ScalarExpressionIR = (
    ScalarLiteralIR
    | ScalarParameterRefIR
    | ScalarUnaryIR
    | ScalarBinaryIR
    | ScalarPowerIR
    | ScalarFunctionIR
)


def _is_scalar_expression(value) -> bool:
    return isinstance(
        value,
        (
            ScalarLiteralIR,
            ScalarParameterRefIR,
            ScalarUnaryIR,
            ScalarBinaryIR,
            ScalarPowerIR,
            ScalarFunctionIR,
        ),
    )


def scalar_parameter_names(
    value: ScalarExpressionIR,
) -> tuple[str, ...]:
    """Return referenced parameter names in deterministic first-use order."""
    if isinstance(value, ScalarParameterRefIR):
        return (value.name,)
    if isinstance(value, ScalarLiteralIR):
        return ()
    if isinstance(value, ScalarUnaryIR):
        return scalar_parameter_names(value.operand)
    if isinstance(value, ScalarPowerIR):
        return scalar_parameter_names(value.base)
    if isinstance(value, ScalarFunctionIR):
        return tuple(
            dict.fromkeys(
                name
                for argument in value.arguments
                for name in scalar_parameter_names(argument)
            )
        )
    if isinstance(value, ScalarBinaryIR):
        return tuple(
            dict.fromkeys(
                (
                    *scalar_parameter_names(value.left),
                    *scalar_parameter_names(value.right),
                )
            )
        )
    raise TypeError("expected ScalarExpressionIR")


def is_affine_scalar_expression(value: ScalarExpressionIR) -> bool:
    """Return whether the bounded #481 dimensional arithmetic can be rendered.

    Addition/subtraction and unary negation preserve the use-site physical role.
    Multiplication/division are portable only when their scale/divisor is an
    authored numeric literal, avoiding derived-unit algebra in this checkpoint.
    """
    if isinstance(value, (ScalarLiteralIR, ScalarParameterRefIR)):
        return True
    if isinstance(value, (ScalarPowerIR, ScalarFunctionIR)):
        return False
    if isinstance(value, ScalarUnaryIR):
        return (
            value.operation == "negate"
            and is_affine_scalar_expression(value.operand)
        )
    if not isinstance(value, ScalarBinaryIR):
        return False

    if value.operation in {"add", "subtract"}:
        return (
            is_affine_scalar_expression(value.left)
            and is_affine_scalar_expression(value.right)
        )

    if value.operation == "multiply":
        return (
            isinstance(value.left, ScalarLiteralIR)
            and is_affine_scalar_expression(value.right)
        ) or (
            isinstance(value.right, ScalarLiteralIR)
            and is_affine_scalar_expression(value.left)
        )

    if value.operation == "divide":
        return (
            is_affine_scalar_expression(value.left)
            and isinstance(value.right, ScalarLiteralIR)
            and value.right.value != 0
        )

    return False


__all__ = [
    "ScalarBinaryIR",
    "ScalarExpressionIR",
    "ScalarFunctionIR",
    "ScalarLiteralIR",
    "ScalarParameterRefIR",
    "ScalarPowerIR",
    "ScalarUnaryIR",
    "is_affine_scalar_expression",
    "scalar_parameter_names",
]
