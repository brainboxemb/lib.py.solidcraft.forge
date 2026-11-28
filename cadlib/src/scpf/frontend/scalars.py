"""Symbolic scalar authoring values and dimension helpers."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from math import isfinite

from ..scalar_ir import (
    ScalarBinaryIR, ScalarExpressionIR, ScalarLiteralIR,
    ScalarParameterRefIR, ScalarPowerIR, ScalarUnaryIR,
)

_PV_TRACKERS = ContextVar("scpf_pv_trackers", default=())

def number_text(value: float) -> str:
    return format(value, "g")

class _NativeExpression(str):
    """Internal SolidCraft expression plus the parameters it depends on."""

    def __new__(cls, value, parameters=()):
        instance = super().__new__(cls, str(value))
        instance.parameters = tuple(dict.fromkeys(parameters))
        return instance

def _native_expression(value, parameters=()):
    inherited = (
        value.parameters
        if isinstance(value, _NativeExpression)
        else ()
    )
    return _NativeExpression(value, (*inherited, *parameters))

def _native_dependencies(value):
    """Return parameter names used by typed native expressions."""
    found = set()
    if isinstance(value, _NativeExpression):
        found.update(value.parameters)
    elif isinstance(value, dict):
        for item in value.values():
            found.update(_native_dependencies(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.update(_native_dependencies(item))
    return frozenset(found)

def _plain_command_value(value):
    """Convert internal expression markers to ordinary JSON-compatible values."""
    if isinstance(value, _NativeExpression):
        return str(value)
    if isinstance(value, dict):
        return {key: _plain_command_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_command_value(item) for item in value]
    if isinstance(value, tuple):
        return [_plain_command_value(item) for item in value]
    return value

def _scalar_ir_value(value) -> ScalarExpressionIR | None:
    """Return authored scalar semantics without parsing compatibility text."""
    if isinstance(value, Parameter):
        return ScalarParameterRefIR(value.name)
    if isinstance(value, Expression):
        return value.scalar_ir
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    ):
        return ScalarLiteralIR(value)
    return None

def _scalar_binary_ir(operation, left, right) -> ScalarExpressionIR | None:
    left_ir = _scalar_ir_value(left)
    right_ir = _scalar_ir_value(right)
    if left_ir is None or right_ir is None:
        return None
    return ScalarBinaryIR(operation, left_ir, right_ir)

def _scalar_power_ir(value, exponent) -> ScalarExpressionIR | None:
    base = _scalar_ir_value(value)
    if base is None:
        return None
    return ScalarPowerIR(base, exponent)

def _scalar_negation_ir(value, *, collapse=False) -> ScalarExpressionIR | None:
    operand = _scalar_ir_value(value)
    if operand is None:
        return None
    if (
        collapse
        and isinstance(operand, ScalarUnaryIR)
        and operand.operation == "negate"
    ):
        return operand.operand
    return ScalarUnaryIR("negate", operand)

@dataclass(frozen=True)
class Parameter:
    """Represent one named editable Forge CAD dimension.

    Parameters:
        name: CAD parameter name. It must be a valid Python identifier.
        value: Current numeric value of the parameter.

    Use when:
        Keep a value symbolic so generated SolidCraft commands can retain an
        editable dependency instead of baking in the current Python number.

    Limits:
        value must be finite. Normal public lower-case model fields are usually
        promoted to parameters automatically, so explicit Parameter() is mainly
        useful in lower-level or assembly code.

    Example:
        wall = Parameter("wall", 2.4)
    """

    name: str
    value: float

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"invalid CAD parameter name: {self.name}")
        if not isinstance(self.value, (int, float)) or not isfinite(self.value):
            raise ValueError(f"invalid CAD parameter value: {self.name}")

    @property
    def expression(self):
        return self.name

    def __index__(self):
        raise TypeError(
            f"{self.name!r} is an editable CAD parameter, not a Python count. "
            f"Use {self.name.upper()} = ... for a fixed constant or "
            f"_{self.name} = ... for a Forge/build-time input used by loops "
            "or other Python-only logic."
        )

    def __truediv__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            if other == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                self.value / other,
                f"{self.name} / {number_text(other)}",
                (self,),
                _scalar_binary_ir("divide", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            divisor = _pv(other)
            if divisor == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                self.value / divisor,
                f"({self.name}) / ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("divide", self, other),
            )
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            if self.value == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                other / self.value,
                f"{number_text(other)} / ({self.name})",
                (self,),
                _scalar_binary_ir("divide", other, self),
            )
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            return Expression(
                self.value * other,
                f"{self.name} * {number_text(other)}",
                (self,),
                _scalar_binary_ir("multiply", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value * _pv(other),
                f"({self.name}) * ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("multiply", self, other),
            )
        return NotImplemented

    __rmul__ = __mul__

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Expression(
                self.value + other,
                f"{self.name} + {number_text(other)} mm",
                (self,),
                _scalar_binary_ir("add", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value + _pv(other),
                f"{self.name} + ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("add", self, other),
            )
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Expression(
                self.value - other,
                f"{self.name} - {number_text(other)} mm",
                (self,),
                _scalar_binary_ir("subtract", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value - _pv(other),
                f"{self.name} - ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("subtract", self, other),
            )
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Expression(
                other - self.value,
                f"{number_text(other)} mm - ({self.name})",
                (self,),
                _scalar_binary_ir("subtract", other, self),
            )
        return NotImplemented

    def __pow__(self, exponent):
        if (
            not isinstance(exponent, (int, float))
            or isinstance(exponent, bool)
            or not isfinite(exponent)
        ):
            return NotImplemented
        return Expression(
            self.value ** exponent,
            f"({self.name}) ^ {number_text(exponent)}",
            (self,),
            _scalar_power_ir(self, exponent),
        )

    def __neg__(self):
        return Expression(
            -self.value,
            f"-({self.name})",
            (self,),
            _scalar_negation_ir(self),
        )

@dataclass(frozen=True)
class Expression:
    value: float
    expression: str
    parameters: tuple[Parameter, ...]
    scalar_ir: ScalarExpressionIR | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __mul__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            return Expression(
                self.value * other,
                f"({self.expression}) * {number_text(other)}",
                self.parameters,
                _scalar_binary_ir("multiply", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value * _pv(other),
                f"({self.expression}) * ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("multiply", self, other),
            )
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            if other == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                self.value / other,
                f"({self.expression}) / {number_text(other)}",
                self.parameters,
                _scalar_binary_ir("divide", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            divisor = _pv(other)
            if divisor == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                self.value / divisor,
                f"({self.expression}) / ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("divide", self, other),
            )
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (float, int)) and not isinstance(other, bool):
            if self.value == 0:
                raise ZeroDivisionError("division by zero")
            return Expression(
                other / self.value,
                f"{number_text(other)} / ({self.expression})",
                self.parameters,
                _scalar_binary_ir("divide", other, self),
            )
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Expression(
                self.value + other,
                f"{self.expression} + {number_text(other)} mm",
                self.parameters,
                _scalar_binary_ir("add", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value + _pv(other),
                f"({self.expression}) + ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("add", self, other),
            )
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Expression(
                self.value - other,
                f"({self.expression}) - {number_text(other)} mm",
                self.parameters,
                _scalar_binary_ir("subtract", self, other),
            )
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value - _pv(other),
                f"({self.expression}) - ({command_value(other)})",
                parameters_in(self, other),
                _scalar_binary_ir("subtract", self, other),
            )
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return Expression(
                other - self.value,
                f"{number_text(other)} mm - ({self.expression})",
                self.parameters,
                _scalar_binary_ir("subtract", other, self),
            )
        return NotImplemented

    def __pow__(self, exponent):
        if (
            not isinstance(exponent, (int, float))
            or isinstance(exponent, bool)
            or not isfinite(exponent)
        ):
            return NotImplemented
        return Expression(
            self.value ** exponent,
            f"({self.expression}) ^ {number_text(exponent)}",
            self.parameters,
            _scalar_power_ir(self, exponent),
        )

    def __neg__(self):
        # Unary minus is used by signed dimensions such as Sketch.extrude(-h).
        # Collapse the exact outer negation form emitted by Forge so converting
        # a negative signed distance back to its positive native magnitude keeps
        # the original symbolic expression instead of producing -(-(h)).
        collapse = (
            self.expression.startswith("-(")
            and self.expression.endswith(")")
        )
        if collapse:
            return Expression(
                -self.value,
                self.expression[2:-1],
                self.parameters,
                _scalar_negation_ir(self, collapse=True),
            )
        return Expression(
            -self.value,
            f"-({self.expression})",
            self.parameters,
            _scalar_negation_ir(self),
        )

def _scaled_direction(direction, distance):
    """Return one cardinal direction scaled by a CAD dimension."""
    from .selectors import _direction_selector\n    vector = _direction_selector(direction).vector
    return tuple(
        0
        if component == 0
        else distance
        if component > 0
        else -distance
        for component in vector
    )

def up(distance):
    """Return a symbolic-safe XYZ offset in the +Z direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = up(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.TOP, distance)

def down(distance):
    """Return a symbolic-safe XYZ offset in the -Z direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = down(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.BOTTOM, distance)

def left(distance):
    """Return a symbolic-safe XYZ offset in the -X direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = left(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.LEFT, distance)

def right(distance):
    """Return a symbolic-safe XYZ offset in the +X direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = right(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.RIGHT, distance)

def front(distance):
    """Return a symbolic-safe XYZ offset in the -Y direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = front(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.FRONT, distance)

def back(distance):
    """Return a symbolic-safe XYZ offset in the +Y direction.

    Parameters:
        distance: Numeric or symbolic CAD distance in mm.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.

    Example:
        offset = back(12)
    """
    from .selectors import Anchor
    return _scaled_direction(Anchor.BACK, distance)

def half(value):
    """Return half of a numeric or symbolic CAD dimension.

    Parameters:
        value: Numeric, Parameter or Expression value to divide by two.

    Use when:
        Keep midpoint-style arithmetic readable without converting a symbolic
        CAD dimension to a concrete Python value.

    Limits:
        Equivalent to value / 2; the input must support that operation.

    Example:
        centre = half(width)
    """
    return value / 2

def midpoint(start, end):
    """Return the midpoint between two numeric or symbolic dimensions.

    Parameters:
        start: First numeric or symbolic coordinate/dimension.
        end: Second numeric or symbolic coordinate/dimension.

    Use when:
        Express a centre position while preserving symbolic CAD dependencies.

    Limits:
        Equivalent to (start + end) / 2; inputs must support symbolic arithmetic.

    Example:
        centre_x = midpoint(left_x, right_x)
    """
    return (start + end) / 2

def _pv(dim) -> float:
    """Read one CAD dimension numerically without recording a user pv() read."""
    if isinstance(dim, Parameter):
        return dim.value
    if isinstance(dim, Expression):
        return dim.value
    if isinstance(dim, (int, float)):
        return float(dim)
    raise TypeError(f"expected a CAD dimension, got {type(dim).__name__}")

@contextmanager
def _track_pv_reads(parameters):
    """Record public pv() reads of these exact Parameter objects."""
    names_by_id = {
        id(parameter): parameter.name
        for parameter in parameters
    }
    reads = set()
    current = _PV_TRACKERS.get()
    token = _PV_TRACKERS.set((*current, (names_by_id, reads)))
    try:
        yield reads
    finally:
        _PV_TRACKERS.reset(token)

def pv(dim) -> float:
    """Return the concrete Python value of a symbolic CAD dimension.

    Parameters:
        dim: Numeric value, Parameter or Expression to read as a Python float.

    Use when:
        Python itself genuinely needs a number for validation or control flow.

    Limits:
        Calling pv() intentionally removes the symbolic dependency at that
        point. Geometry and placement should normally keep Parameter/Expression
        objects symbolic so backend lowering can preserve editable native CAD
        dependencies.

    Example:
        if pv(clearance) < 0:
            raise ValueError("clearance must not be negative")
    """
    for parameter in parameters_in(dim):
        parameter_id = id(parameter)
        for names_by_id, reads in _PV_TRACKERS.get():
            name = names_by_id.get(parameter_id)
            if name is not None:
                reads.add(name)
    return _pv(dim)

def command_value(dim):
    if isinstance(dim, Parameter):
        return _native_expression(dim.expression, (dim.name,))
    if isinstance(dim, Expression):
        return _native_expression(
            dim.expression,
            tuple(parameter.name for parameter in dim.parameters),
        )
    return dim

def parameters_in(*values) -> tuple[Parameter, ...]:
    found = {}
    for value in values:
        if isinstance(value, Parameter):
            found.setdefault(value.name, value)
        elif isinstance(value, Expression):
            for param in value.parameters:
                found.setdefault(param.name, param)
        elif isinstance(value, _BoundOffset):
            for param in parameters_in(value.delta):
                found.setdefault(param.name, param)
    return tuple(found.values())

def _dim_add(left, right):
    """Add CAD dimensions without turning a zero into noisy expressions."""
    if left == 0:
        return right
    if right == 0:
        return left
    return left + right

def _dim_sub(left, right):
    """Subtract CAD dimensions while preserving Parameter/Expression intent."""
    if right == 0:
        return left
    if left == 0:
        return -right
    return left - right

def _dim_abs(value):
    """Return a positive CAD distance while preserving symbolic dependencies."""

    if isinstance(value, Parameter):
        return Expression(
            abs(value.value),
            f"abs({value.name})",
            (value,),
        )
    if isinstance(value, Expression):
        return Expression(
            abs(value.value),
            f"abs({value.expression})",
            value.parameters,
        )
    return abs(value)
