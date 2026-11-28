"""Symbolic CAD math that preserves native SolidCraft parameter dependencies."""

import builtins
import math

from .core import (
    Expression,
    Parameter,
    _pv,
    _scalar_ir_value,
    command_value,
    number_text,
    parameters_in,
)
from .scalar_ir import ScalarFunctionIR


def _validated(value):
    if isinstance(value, (Parameter, Expression)):
        return value
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    ):
        return value
    raise TypeError("cadmath values must be finite numbers, Parameter or Expression")


def _text(value):
    value = _validated(value)
    if isinstance(value, (Parameter, Expression)):
        return str(command_value(value))
    return number_text(value)


def _result(name, values, current):
    values = tuple(_validated(value) for value in values)
    parameters = parameters_in(*values)
    if not parameters:
        return current
    scalar_arguments = tuple(_scalar_ir_value(value) for value in values)
    scalar_ir = (
        ScalarFunctionIR(name, scalar_arguments)
        if all(value is not None for value in scalar_arguments)
        else None
    )
    return Expression(
        float(current),
        f"{name}(" + ",".join(_text(value) for value in values) + ")",
        parameters,
        scalar_ir,
    )


def min(*values):
    """Return the smallest CAD value while preserving symbolic dependencies."""
    if len(values) < 2:
        raise TypeError("cadmath.min requires at least two values")
    checked = tuple(_validated(value) for value in values)
    return _result("min", checked, builtins.min(_pv(value) for value in checked))


def max(*values):
    """Return the largest CAD value while preserving symbolic dependencies."""
    if len(values) < 2:
        raise TypeError("cadmath.max requires at least two values")
    checked = tuple(_validated(value) for value in values)
    return _result("max", checked, builtins.max(_pv(value) for value in checked))


def sqrt(value):
    """Return the positive square root as a native symbolic expression."""
    value = _validated(value)
    return _result("sqrt", (value,), math.sqrt(_pv(value)))


def abs(value):
    """Return the absolute CAD value as a native symbolic expression."""
    value = _validated(value)
    return _result("abs", (value,), builtins.abs(_pv(value)))


def round(value):
    """Round to the nearest integer using SolidCraft's native round()."""
    value = _validated(value)
    return _result("round", (value,), builtins.round(_pv(value)))


def floor(value):
    """Round downward to an integer using SolidCraft's native floor()."""
    value = _validated(value)
    return _result("floor", (value,), math.floor(_pv(value)))


def atan(value):
    """Return native atan() in degrees, matching SolidCraft CAD expressions."""
    value = _validated(value)
    return _result(
        "atan",
        (value,),
        math.degrees(math.atan(_pv(value))),
    )


__all__ = ["min", "max", "sqrt", "abs", "round", "floor", "atan"]
