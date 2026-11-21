"""Symbolic dimensions and model nodes. No SolidCraft transport or geometry.

All unadorned numerical values are millimetres. Model function arguments
become named parameters by the runner, not by user-written decorators.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any


_PV_TRACKERS = ContextVar("scpf_pv_trackers", default=())


def number_text(value: float) -> str:
    return format(value, "g")


@dataclass(frozen=True)
class _DirectionSelector:
    """BOSL2-style cardinal selector used for faces, edges and anchors."""

    vector: tuple[int, int, int]

    def __post_init__(self):
        if (
            not isinstance(self.vector, (tuple, list))
            or len(self.vector) != 3
            or any(value not in (-1, 0, 1) for value in self.vector)
        ):
            raise ValueError("direction selector must contain three -1/0/1 values")
        object.__setattr__(self, "vector", tuple(self.vector))

    def __add__(self, other):
        return _combine_direction_selectors(self, other)


class Anchor(str, Enum):
    """Select component attachment references and cardinal directions.

    Use when:
        Use cardinal or corner anchors to attach reusable component
        occurrences, or combine cardinal values to identify Box edges/corners.

    Limits:
        Anchor is the assembly/alignment vocabulary. Within-component feature
        placement normally uses Faces instead. INNER_BOTTOM has no direction
        vector and therefore cannot be used as a cardinal selector.
    """
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"
    FRONT_TOP_LEFT = "front_top_left"
    FRONT_TOP_RIGHT = "front_top_right"
    FRONT_BOTTOM_LEFT = "front_bottom_left"
    FRONT_BOTTOM_RIGHT = "front_bottom_right"
    BACK_TOP_LEFT = "back_top_left"
    BACK_TOP_RIGHT = "back_top_right"
    BACK_BOTTOM_LEFT = "back_bottom_left"
    BACK_BOTTOM_RIGHT = "back_bottom_right"
    INNER_BOTTOM = "inner_bottom"

    UP = TOP
    DOWN = BOTTOM

    @property
    def vector(self) -> tuple[float, float, float]:
        """Return the 3-D direction/selector vector for this anchor."""
        vectors = {
            Anchor.CENTER: (0.0, 0.0, 0.0),
            Anchor.TOP: (0.0, 0.0, 1.0),
            Anchor.BOTTOM: (0.0, 0.0, -1.0),
            Anchor.LEFT: (-1.0, 0.0, 0.0),
            Anchor.RIGHT: (1.0, 0.0, 0.0),
            Anchor.FRONT: (0.0, -1.0, 0.0),
            Anchor.BACK: (0.0, 1.0, 0.0),
            Anchor.FRONT_TOP_LEFT: (-1.0, -1.0, 1.0),
            Anchor.FRONT_TOP_RIGHT: (1.0, -1.0, 1.0),
            Anchor.FRONT_BOTTOM_LEFT: (-1.0, -1.0, -1.0),
            Anchor.FRONT_BOTTOM_RIGHT: (1.0, -1.0, -1.0),
            Anchor.BACK_TOP_LEFT: (-1.0, 1.0, 1.0),
            Anchor.BACK_TOP_RIGHT: (1.0, 1.0, 1.0),
            Anchor.BACK_BOTTOM_LEFT: (-1.0, 1.0, -1.0),
            Anchor.BACK_BOTTOM_RIGHT: (1.0, 1.0, -1.0),
        }
        if self not in vectors:
            raise ValueError(f"Anchor.{self.name} has no direction vector")
        return vectors[self]

    def __add__(self, other):
        return _combine_direction_selectors(self, other)


def _direction_selector(value):
    if isinstance(value, _DirectionSelector):
        return value
    if isinstance(value, Anchor):
        return _DirectionSelector(tuple(int(v) for v in value.vector))
    if isinstance(value, str):
        try:
            return _direction_selector(Anchor(value))
        except ValueError as exc:
            raise ValueError(f"unknown direction selector: {value!r}") from exc
    raise TypeError("direction selector must use TOP/BOTTOM/LEFT/RIGHT/FRONT/BACK")


def _combine_direction_selectors(left, right):
    left = _direction_selector(left)
    right = _direction_selector(right)
    combined = []
    for a, b in zip(left.vector, right.vector):
        if a and b:
            raise ValueError("direction selectors cannot specify the same axis twice")
        combined.append(a or b)
    return _DirectionSelector(tuple(combined))


def _selector_rank(value):
    return sum(component != 0 for component in _direction_selector(value).vector)


def _selector_anchor(value):
    """Resolve a composable cardinal selector to a standard Anchor."""
    selector = _direction_selector(value)
    for anchor in Anchor:
        try:
            vector = tuple(int(component) for component in anchor.vector)
        except ValueError:
            continue
        if vector == selector.vector:
            return anchor
    raise ValueError(
        f"direction selector {selector.vector!r} is not a standard assembly anchor"
    )


@dataclass(frozen=True)
class AnchorFrame:
    """Describe one local attachment point and orientation.

    Parameters:
        origin: Component-local XYZ attachment point in mm. Defaults to (0, 0, 0).
        z: Attachment-normal direction as an XYZ vector or Anchor. Defaults to Anchor.UP.
        x: Local X/clocking direction as an XYZ vector or Anchor. Defaults to Anchor.RIGHT.

    Use when:
        A standard face or corner Anchor is not enough and the mounting datum
        needs its own local origin plus orientation. A reusable component may
        expose named AnchorFrame values from anchors(), or an assembly may pass
        one directly to attach().

    Limits:
        z and x must be non-zero and must not be parallel. Direct frames on
        explicitly rotated occurrences have limited support as documented by
        the assembly guide.

    Example:
        mount = AnchorFrame(origin=(20, 0, 10), z=Anchor.FRONT, x=Anchor.RIGHT)
    """

    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    z: tuple[float, float, float] | Anchor = Anchor.UP
    x: tuple[float, float, float] | Anchor = Anchor.RIGHT

    def __post_init__(self):
        vectors = {}
        for name, value in (
            ("origin", self.origin),
            ("z", self.z),
            ("x", self.x),
        ):
            if isinstance(value, Anchor):
                value = value.vector
            if not isinstance(value, (tuple, list)) or len(value) != 3:
                raise ValueError(f"AnchorFrame {name} must be an XYZ triple")
            if any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not isfinite(v)
                for v in value
            ):
                raise ValueError(
                    f"AnchorFrame {name} must contain finite numeric values"
                )
            vectors[name] = tuple(float(v) for v in value)

        z = vectors["z"]
        x = vectors["x"]
        if sum(v * v for v in z) <= 0 or sum(v * v for v in x) <= 0:
            raise ValueError("AnchorFrame x and z directions must be non-zero")
        cross = (
            z[1] * x[2] - z[2] * x[1],
            z[2] * x[0] - z[0] * x[2],
            z[0] * x[1] - z[1] * x[0],
        )
        if sum(v * v for v in cross) <= 1e-18:
            raise ValueError("AnchorFrame x direction must not be parallel to z")

        object.__setattr__(self, "origin", vectors["origin"])
        object.__setattr__(self, "z", z)
        object.__setattr__(self, "x", x)


@dataclass(frozen=True)
class AnchorTopology:
    """Describe an attachment datum that follows native SolidCraft topology.

    Parameters:
        edge: XYZ pick point on the target edge, in component-local mm.
        on: XYZ pick point on the adjacent planar face, in component-local mm.
        corner: Optional XYZ endpoint/corner pick in component-local mm.
        z: Optional non-zero XYZ attachment-normal override.
        x: Optional non-zero XYZ clocking-direction override.

    Use when:
        A relationship should follow a particular edge, adjacent planar face
        and optionally one endpoint as dimensions change, rather than freezing
        one XYZ coordinate.

    Limits:
        edge and on are native selection pick points. Current Forge support
        focuses on planar-face edges and non-rotated occurrences. z and x, when
        both supplied, must not be parallel.

    Example:
        mount = AnchorTopology(edge=(0, 25, 10), on=(0, 20, 10), corner=(0, 25, 0))
    """

    edge: tuple[float, float, float]
    on: tuple[float, float, float]
    corner: tuple[float, float, float] | None = None
    z: tuple[float, float, float] | None = None
    x: tuple[float, float, float] | None = None

    def __post_init__(self):
        for name in ("edge", "on", "corner", "z", "x"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, (tuple, list)) or len(value) != 3:
                raise ValueError(f"AnchorTopology {name} must be an XYZ triple")
            if any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not isfinite(v)
                for v in value
            ):
                raise ValueError(
                    f"AnchorTopology {name} must contain finite numeric values"
                )
            object.__setattr__(self, name, tuple(float(v) for v in value))

        if self.z is not None and sum(v * v for v in self.z) <= 0:
            raise ValueError("AnchorTopology z direction must be non-zero")
        if self.x is not None and sum(v * v for v in self.x) <= 0:
            raise ValueError("AnchorTopology x direction must be non-zero")
        if self.z is not None and self.x is not None:
            cross = (
                self.z[1] * self.x[2] - self.z[2] * self.x[1],
                self.z[2] * self.x[0] - self.z[0] * self.x[2],
                self.z[0] * self.x[1] - self.z[1] * self.x[0],
            )
            if sum(v * v for v in cross) <= 1e-18:
                raise ValueError(
                    "AnchorTopology x direction must not be parallel to z"
                )


class Depth(str, Enum):
    """Choose a supported feature-depth policy.

    Use when:
        Use Depth.THROUGH_ALL for features such as Hole that should pass
        completely through their target instead of using a fixed distance.

    Limits:
        THROUGH_ALL is currently the only named depth policy.
    """
    THROUGH_ALL = "through_all"


class Axis(str, Enum):
    """Select one of the native principal X, Y or Z axes.

    Use when:
        Use Axis for primitive orientation and supported patterns, for example
        Cylinder(..., axis=Axis.X) or a linear Hole pattern along Axis.Y.

    Limits:
        Axis is a principal-axis selector, not an attachment reference and not
        an extrusion Direction.
    """
    X = "X"
    Y = "Y"
    Z = "Z"


class Edges(Enum):
    """Select edges for supported fillet and chamfer feature operations.

    Use when:
        Use Edges.VERTICAL for the vertical edges of a supported rectangular
        body. Use from_profile() for named profile segments and from_vertices()
        for extrusion-axis edges grown from named profile vertices.

    Limits:
        Only the selectors implemented here are public. from_profile()
        currently supports sides="both"; from_vertices() requires named
        Polygon2D vertices.
    """
    VERTICAL = "vertical"

    @staticmethod
    def from_profile(*segment_ids, sides="both"):
        """Select named 2D sketch segments on the broad faces of an extrusion.

        IDs are defined by Polygon2D(ids=...). At compilation time SCPF
        resolves them into points accepted by SolidCraft's fillet/chamfer API.
        Wildcards (e.g. "outer_*") match sketch IDs, not 3D edge names.
        """
        if not segment_ids or any(not isinstance(name, str) or not name
                                  for name in segment_ids):
            raise ValueError("provide one or more profile segment IDs or patterns")
        if sides != "both":
            raise ValueError("profile-edge selection currently supports sides='both'")
        return _ProfileEdgeSelection(tuple(segment_ids), sides)

    @staticmethod
    def from_vertices(*vertex_ids):
        """Select extrusion-axis edges grown from named profile vertices."""
        if not vertex_ids or any(not isinstance(name, str) or not name
                                 for name in vertex_ids):
            raise ValueError("provide named profile vertices")
        return _ProfileEdgeSelection(tuple(vertex_ids), "axis", "vertices")


@dataclass(frozen=True)
class _ProfileEdgeSelection:
    patterns: tuple[str, ...]
    sides: str
    kind: str = "segments"


def _feature_edge_selection(edges, *, operation):
    """Validate one public fillet/chamfer edge selection."""
    if edges is Edges.VERTICAL or isinstance(edges, _ProfileEdgeSelection):
        return edges

    directional = (
        isinstance(edges, (_DirectionSelector, Anchor))
        or (
            isinstance(edges, (list, tuple))
            and edges
            and all(
                isinstance(edge, (_DirectionSelector, Anchor))
                for edge in edges
            )
        )
    )
    if directional:
        selectors = (
            (edges,)
            if isinstance(edges, (_DirectionSelector, Anchor))
            else tuple(edges)
        )
        if any(_selector_rank(edge) != 2 for edge in selectors):
            raise ValueError(
                f"{operation} Box edge selectors must combine exactly two "
                "cardinal directions"
            )
        return selectors

    if not isinstance(edges, (list, tuple)) or not edges:
        raise ValueError(
            f"{operation} edges must use Edges.VERTICAL, supported named "
            "selectors or a non-empty sequence of 3D edge points"
        )
    for point in edges:
        if not isinstance(point, (list, tuple)) or len(point) != 3:
            raise ValueError(
                f"each {operation} edge point must have x, y and z"
            )
        for coordinate in point:
            _pv(coordinate)
    return edges


class Faces(Enum):
    """Select named planar faces for within-component feature operations.

    Use when:
        Pass a Faces value to operations such as Shape.on() and Shape.shell()
        to identify a surface of the target body.

    Limits:
        The enum defines all six cardinal faces. Individual operations may
        support only a subset; Shape.on() currently accepts TOP and BOTTOM.
        Component assembly attachment uses Anchor instead.
    """
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"


@dataclass(frozen=True)
class _BoundOffset:
    """Position relative to one named axis of the parent bounds."""
    axis: str
    reference: str
    delta: Any = 0

    def __add__(self, value):
        if isinstance(value, bool):
            return NotImplemented
        delta = value if self.delta == 0 else self.delta + value
        return _BoundOffset(self.axis, self.reference, delta)

    __radd__ = __add__

    def __sub__(self, value):
        if isinstance(value, bool):
            return NotImplemented
        delta = -value if self.delta == 0 else self.delta - value
        return _BoundOffset(self.axis, self.reference, delta)


class _AxisRef(str):
    """Axis token with MIN, CENTER and MAX parent-bound placement selectors.

    Use when:
        Public X, Y and Z tokens let feature offsets refer to a parent bound,
        for example X.MIN + 10 or Y.MAX - 10, without hard-coding the current
        global coordinate.

    Limits:
        These X/Y/Z tokens are bound selectors, not Axis.X/Y/Z primitive-axis
        enum values.
    """

    @property
    def MIN(self):
        return _BoundOffset(str(self), "min")

    @property
    def CENTER(self):
        return _BoundOffset(str(self), "center")

    @property
    def MAX(self):
        return _BoundOffset(str(self), "max")


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


@dataclass(frozen=True)
class Parameter:
    """Represent one named editable CAD dimension.

    Parameters:
        name: SolidCraft parameter name. It must be a valid Python identifier.
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

    def __truediv__(self, other: float):
        if not isinstance(other, (float, int)) or other == 0:
            return NotImplemented
        return Expression(self.value / other, f"{self.name} / {number_text(other)}", (self,))

    def __mul__(self, other: float):
        if not isinstance(other, (float, int)):
            return NotImplemented
        return Expression(self.value * other, f"{self.name} * {number_text(other)}", (self,))

    __rmul__ = __mul__

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Expression(self.value + other,
                              f"{self.name} + {number_text(other)} mm", (self,))
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value + _pv(other),
                f"{self.name} + ({command_value(other)})",
                parameters_in(self, other),
            )
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Expression(self.value - other,
                              f"{self.name} - {number_text(other)} mm", (self,))
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value - _pv(other),
                f"{self.name} - ({command_value(other)})",
                parameters_in(self, other),
            )
        return NotImplemented

    def __neg__(self):
        return Expression(-self.value, f"-({self.name})", (self,))


@dataclass(frozen=True)
class Expression:
    value: float
    expression: str
    parameters: tuple[Parameter, ...]

    def __mul__(self, other):
        if not isinstance(other, (float, int)):
            return NotImplemented
        return Expression(self.value * other,
                          f"({self.expression}) * {number_text(other)}", self.parameters)

    __rmul__ = __mul__

    def __truediv__(self, other: float):
        if not isinstance(other, (float, int)) or other == 0:
            return NotImplemented
        return Expression(self.value / other, f"({self.expression}) / {number_text(other)}", self.parameters)

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Expression(self.value + other,
                              f"{self.expression} + {number_text(other)} mm",
                              self.parameters)
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value + _pv(other),
                f"({self.expression}) + ({command_value(other)})",
                parameters_in(self, other),
            )
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Expression(self.value - other,
                              f"({self.expression}) - {number_text(other)} mm", self.parameters)
        if isinstance(other, (Parameter, Expression)):
            return Expression(
                self.value - _pv(other),
                f"({self.expression}) - ({command_value(other)})",
                parameters_in(self, other),
            )
        return NotImplemented

    def __neg__(self):
        # Unary minus is used by signed dimensions such as Sketch.extrude(-h).
        # Collapse the exact outer negation form emitted by Forge so converting
        # a negative signed distance back to its positive native magnitude keeps
        # the original symbolic expression instead of producing -(-(h)).
        if self.expression.startswith("-(") and self.expression.endswith(")"):
            return Expression(
                -self.value,
                self.expression[2:-1],
                self.parameters,
            )
        return Expression(-self.value, f"-({self.expression})", self.parameters)


def _scaled_direction(direction, distance):
    """Return one cardinal direction scaled by a CAD dimension."""
    vector = _direction_selector(direction).vector
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
        objects symbolic so SolidCraft remains editable and associative.

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


def _box_corner_from_anchor(length, width, height, point, anchor):
    """Return the native Box corner when one box anchor is placed at point."""
    vector = _direction_selector(anchor).vector
    dimensions = (length, width, height)
    corner = []
    for coordinate, dimension, side in zip(point, dimensions, vector):
        if side < 0:
            corner.append(coordinate)
        elif side > 0:
            corner.append(_dim_add(coordinate, -dimension))
        else:
            corner.append(_dim_add(coordinate, -half(dimension)))
    return tuple(corner)


def _primitive_center_from_anchor(extents, point, anchor):
    """Resolve a primitive's center from an anchor on its world XYZ bounds."""
    vector = _direction_selector(anchor).vector
    return tuple(
        _dim_add(coordinate, (
            half(extent) if side < 0 else
            -half(extent) if side > 0 else 0
        ))
        for coordinate, extent, side in zip(point, extents, vector)
    )


def _cylinder_base_from_anchor(height, diameter, axis, point, anchor):
    """Get native cylinder base from its selected world-space anchor.

    The axial dimension is height; the two transverse dimensions are
    diameter. CENTER therefore places the base half a height behind origin.
    """
    extents = {
        "X": (height, diameter, diameter),
        "Y": (diameter, height, diameter),
        "Z": (diameter, diameter, height),
    }[axis]
    center = _primitive_center_from_anchor(extents, point, anchor)
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    base = list(center)
    base[index] = _dim_add(base[index], -half(height))
    return tuple(base)


def _cone_base_from_anchor(height, axis, point, anchor):
    """Get native cone/frustum base from an axial anchor datum.

    A tapered solid has different transverse radii at its two ends, so Forge
    keeps Cone anchors deliberately unambiguous: CENTER or either axial end.
    """
    selector = _direction_selector(anchor)
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    if any(side != 0 for i, side in enumerate(selector.vector) if i != index):
        raise ValueError(
            "Cone anchor must be CENTER or an axial end for the selected axis"
        )
    base = list(point)
    axial_side = selector.vector[index]
    if axial_side > 0:
        base[index] = _dim_add(base[index], -height)
    elif axial_side == 0:
        base[index] = _dim_add(base[index], -half(height))
    return tuple(base)


def _sphere_center_from_anchor(radius, point, anchor):
    """Place the selected sphere tangent/center anchor at a world point."""
    vector = _direction_selector(anchor).vector
    return tuple(
        _dim_add(coordinate, radius if side < 0 else -radius if side > 0 else 0)
        for coordinate, side in zip(point, vector)
    )


def _shape_center(shape):
    """Return the nominal CENTER anchor of a direct CSG shape.

    Boolean composites are accepted only when both operands have the same
    center. This keeps CENTER alignment deterministic without inventing a
    general bounding-box/geometry solver in Forge.
    """
    if not isinstance(shape, Shape):
        raise TypeError("align() target must be a Shape")

    if shape.kind == "box":
        length, width, height, anchor = shape.data
        dimensions = (length, width, height)
        return tuple(
            half(dimension) if side < 0
            else -half(dimension) if side > 0
            else 0
            for dimension, side in zip(dimensions, anchor.vector)
        )

    if shape.kind == "sphere":
        radius, anchor = shape.data
        return _sphere_center_from_anchor(radius, (0, 0, 0), anchor)

    if shape.kind == "cylinder":
        height, diameter, axis, anchor = shape.data
        extents = {
            "X": (height, diameter, diameter),
            "Y": (diameter, height, diameter),
            "Z": (diameter, diameter, height),
        }[axis]
        return _primitive_center_from_anchor(extents, (0, 0, 0), anchor)

    if shape.kind == "cone":
        height, _diameter, _top_diameter, axis, anchor = shape.data
        base = _cone_base_from_anchor(height, axis, (0, 0, 0), anchor)
        index = {"X": 0, "Y": 1, "Z": 2}[axis]
        center = list(base)
        center[index] = _dim_add(center[index], half(height))
        return tuple(center)

    if shape.kind == "translated":
        child, delta = shape.data
        center = _shape_center(child)
        return tuple(_dim_add(center[i], delta[i]) for i in range(3))

    if shape.kind == "placed3d":
        child, x, y, z = shape.data
        if child.kind != "cylinder":
            raise ValueError("CENTER alignment only supports placed Cylinder CSG shapes")
        center = _shape_center(child)
        base = (x, y, z)
        return tuple(_dim_add(base[i], center[i]) for i in range(3))

    if shape.kind in ("intersection", "union"):
        left, right = shape.data
        left_center = _shape_center(left)
        right_center = _shape_center(right)
        if left_center != right_center:
            raise ValueError(
                "CENTER alignment of a CSG composite requires operands "
                "with the same center"
            )
        return left_center

    raise ValueError(
        "CENTER alignment currently supports direct Box, Sphere, Cylinder, Cone "
        "and centered CSG composites"
    )


def _pattern_direction(value, label):
    """Convert one public pattern direction to a native XYZ vector."""
    try:
        axis = Axis(value)
    except (TypeError, ValueError):
        axis = None
    if axis is not None:
        return {
            Axis.X: (1.0, 0.0, 0.0),
            Axis.Y: (0.0, 1.0, 0.0),
            Axis.Z: (0.0, 0.0, 1.0),
        }[axis]
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise TypeError(f"{label} must be Axis.X/Y/Z or an XYZ direction")
    if any(
        isinstance(component, bool)
        or not isinstance(component, (int, float))
        or not isfinite(component)
        for component in value
    ):
        raise ValueError(f"{label} must contain finite numeric values")
    vector = tuple(float(component) for component in value)
    if sum(component * component for component in vector) <= 0:
        raise ValueError(f"{label} must be non-zero")
    return vector


def _pattern_count(value, label):
    """Validate a native pattern count and keep direct parameters unitless."""
    if isinstance(value, Parameter):
        numeric = value.value
        if numeric < 1 or not float(numeric).is_integer():
            raise ValueError(f"{label} must currently evaluate to a positive integer")
        return value
    if isinstance(value, Expression):
        raise TypeError(
            f"{label} expressions are not supported yet; use a direct model "
            "parameter or a fixed integer"
        )
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer or direct Parameter")
    return value


def _pattern_angle(value, label):
    """Validate an optional circular-pattern angle in degrees."""
    if value is None:
        return None
    if isinstance(value, Parameter):
        numeric = value.value
    elif isinstance(value, Expression):
        raise TypeError(
            f"{label} expressions are not supported yet; use a direct model "
            "parameter or a fixed number of degrees"
        )
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number of degrees or direct Parameter")
    else:
        numeric = value
    if not isfinite(numeric) or not 0 < numeric <= 360:
        raise ValueError(f"{label} must be above 0 and at most 360 degrees")
    return value


def _circular_pattern_axis(axis, origin):
    """Validate one fixed circular-pattern axis."""
    try:
        principal = Axis(axis)
    except (TypeError, ValueError):
        principal = None
    if principal is not None and origin is None:
        return principal.value

    direction = _pattern_direction(axis, "circular_pattern axis")
    if origin is None:
        origin = (0, 0, 0)
    if not isinstance(origin, (tuple, list)) or len(origin) != 3:
        raise ValueError("circular_pattern origin must be an XYZ point")
    for coordinate in origin:
        if isinstance(coordinate, bool) or not isfinite(_pv(coordinate)):
            raise ValueError(
                "circular_pattern origin must contain finite numeric dimensions"
            )
    return (tuple(origin), direction)


def _shape_contains(root, needle):
    """Return whether the exact source Shape is already in a feature tree."""
    if root is needle:
        return True
    if isinstance(root, Shape):
        return _shape_contains(root.data, needle)
    if isinstance(root, (tuple, list)):
        return any(_shape_contains(item, needle) for item in root)
    return False


def _feature_pattern_sources(root, feature, operation):
    """Validate shared source-feature rules for native feature patterns."""
    if isinstance(feature, Shape):
        sources = (feature,)
    elif isinstance(feature, (tuple, list)) and feature:
        if not all(isinstance(item, Shape) for item in feature):
            raise TypeError(f"{operation} feature list must contain Shapes")
        sources = tuple(feature)
    else:
        raise TypeError(f"{operation} requires a source feature Shape")

    if any(source.kind != "explicit_sketch_extrusion" for source in sources):
        raise ValueError(
            f"{operation} currently supports features produced by "
            "Sketch.extrude()"
        )
    if any(not _shape_contains(root, source) for source in sources):
        raise ValueError(
            f"{operation} source feature must already be applied to this Shape"
        )
    return sources


@dataclass(frozen=True)
class Shape:
    """Store Forge geometry and feature operations before SolidCraft executes them.

    Parameters:
        kind: Forge node type. Public constructors set this; normal model code should not invent kind values.
        data: Data stored for that node type. Public constructors and methods build this payload.

    Use when:
        Shape values are normally returned by constructors such as Box(),
        Cylinder(), Hole() and Sketch.extrude(), then transformed or combined
        with the supported Shape methods/operators.

    Limits:
        Shape is only Forge's description of the model. SolidCraft owns the final
        BRep and feature history; users normally do not instantiate
        Shape(kind, data) directly.

    Example:
        body = Box(80, 50, 12)
    """

    kind: str
    data: Any

    def __getattr__(self, name):
        if name == "group":
            raise AttributeError(
                "Shape has no group(). group() changes SolidCraft browser "
                "hierarchy for component occurrences or Assemblies. Keep one "
                "physical part's geometry as a Shape; model separate physical "
                "parts as components/occurrences."
            )
        raise AttributeError(f"Shape has no attribute {name!r}")

    def _csg_operand(self, other, operator):
        other = _shape(other)
        if (
            self.kind == "material_assignment"
            or other.kind == "material_assignment"
        ):
            raise TypeError(
                f"material-assigned Shapes cannot be combined with {operator}. "
                "Finish one physical part's Shape geometry before calling "
                "with_material(). For separate physical parts or different "
                "materials, use component occurrences in an Assembly."
            )
        return other

    def __and__(self, other):
        return Shape("intersection", (self, self._csg_operand(other, "&")))

    def __add__(self, other):
        return Shape("union", (self, self._csg_operand(other, "+")))

    def __or__(self, other):
        return self + other

    def __sub__(self, other):
        return Shape("difference", (self, self._csg_operand(other, "-")))

    def move(self, x=0, y=0, z=0):
        """Translate a CSG shape by millimetres.

        Translates all primitives in a composite CSG model together.
        General feature-based box placement is not implemented yet.
        """
        offsets = (_pv(x), _pv(y), _pv(z))
        if not all(isfinite(v) for v in offsets):
            raise ValueError("move() requires finite coordinates")
        if self.kind in ("fillet", "shell", "rectangular_pattern", "circular_pattern"):
            raise ValueError("move() currently supports only primitive and CSG shapes")
        return Shape("translated", (self, offsets))

    def taper(self, *, from_z, inset):
        """Make a box with a flat front and continuously tapered rear walls.

        from_z is measured from the Box bottom face, independent of the Box
        anchor. The rear perimeter retreats by inset per side from that section
        to the Box top face. This produces native editable sketches and loft.
        """
        if self.kind != "box":
            raise ValueError("taper() currently requires a Box")
        width, height, depth, _anchor = self.data
        if not 0 < _pv(from_z) < _pv(depth):
            raise ValueError("taper from_z must lie within the box depth")
        if not 0 < _pv(inset) * 2 < min(_pv(width), _pv(height)):
            raise ValueError("taper inset must be below half the footprint")
        return Shape("tapered_box", (self, from_z, inset))

    def fold(
        self,
        *,
        line,
        angle=90,
        fixed=None,
        position="centerline",
        flip=False,
    ):
        """Fold existing sheet material along one straight line.

        Parameters:
            line: Two XY or XYZ points defining the fold line.
            angle: Bend angle in degrees. Defaults to 90.
            fixed: Optional XYZ point on the side that must stay fixed.
            position: Native bend-line position: "centerline", "start", "end" or "mould". Defaults to "centerline".
            flip: Fold to the opposite side when True. Defaults to False.

        Use when:
            Bend material that already exists in a sheet blank. Dimensions and
            bend allowance come from the sheet's shared rule.

        Limits:
            This first qualified form supports one straight fold line. The line
            endpoints and fixed point are fixed finite coordinates.

        Example:
            sheet.fold(
                line=((20, -20), (20, 20)),
                angle=90,
                fixed=(-20, 0, 0),
            )
        """
        if not isinstance(line, (list, tuple)) or len(line) != 2:
            raise ValueError("fold line must contain exactly two points")

        def point3(value, label):
            if not isinstance(value, (list, tuple)) or len(value) not in (2, 3):
                raise ValueError(f"{label} must be an XY or XYZ point")
            result = tuple(value) if len(value) == 3 else (value[0], value[1], 0)
            if not all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in result
            ):
                raise ValueError(
                    f"{label} coordinates must be fixed numbers; "
                    "associative fold lines require a Sketch line"
                )
            if not all(isfinite(v) for v in result):
                raise ValueError(f"{label} must contain finite coordinates")
            return result

        p0 = point3(line[0], "fold line point")
        p1 = point3(line[1], "fold line point")
        if tuple(_pv(v) for v in p0) == tuple(_pv(v) for v in p1):
            raise ValueError("fold line points must be different")

        value = _pv(angle)
        if not isfinite(value) or value == 0 or abs(value) >= 180:
            raise ValueError("fold angle must be non-zero and below 180 degrees")

        if position not in ("centerline", "start", "end", "mould"):
            raise ValueError(
                "fold position must be centerline, start, end or mould"
            )
        if not isinstance(flip, bool):
            raise TypeError("fold flip must be True or False")

        fixed_point = None if fixed is None else point3(fixed, "fold fixed")
        return Shape(
            "sheet_fold",
            (self, (p0, p1), angle, fixed_point, position, flip),
        )

    def fillet(self, radius, *, edges=Edges.VERTICAL):
        """Round selected solid edges with one radius.

        Parameters:
            radius: Fillet radius in mm.
            edges: Edge selection. Use Edges.VERTICAL, a supported two-direction Box edge selector such as FRONT + LEFT, Edges.from_profile(...), Edges.from_vertices(...) or a non-empty sequence of XYZ edge pick points. Defaults to Edges.VERTICAL.

        Use when:
            Round one or more edges of a supported feature-based body. Fillet
            and chamfer use the same edge-selection forms.

        Limits:
            Edges.VERTICAL and cardinal Box edge selectors require a supported
            rectangular body. Named profile/vertex selectors require matching
            Polygon2D ids in a supported extrusion.

        Example:
            body = Box(80, 50, 15)
            rounded = body.fillet(3, edges=Edges.VERTICAL)
        """
        _pv(radius)
        return Shape(
            "fillet",
            (self, radius, _feature_edge_selection(edges, operation="fillet")),
        )

    def chamfer(self, distance, *, edges=Edges.VERTICAL):
        """Chamfer selected solid edges by one equal distance.

        Parameters:
            distance: Chamfer distance in mm.
            edges: Edge selection. Use Edges.VERTICAL, a supported two-direction Box edge selector such as FRONT + LEFT, Edges.from_profile(...), Edges.from_vertices(...) or a non-empty sequence of XYZ edge pick points. Defaults to Edges.VERTICAL.

        Use when:
            Bevel one or more edges of a supported feature-based body. Chamfer
            and fillet use the same edge-selection forms.

        Limits:
            Edges.VERTICAL and cardinal Box edge selectors require a supported
            rectangular body. Named profile/vertex selectors require matching
            Polygon2D ids in a supported extrusion.

        Example:
            body = Box(80, 50, 15)
            bevelled = body.chamfer(3, edges=Edges.VERTICAL)
        """
        _pv(distance)
        return Shape(
            "chamfer",
            (self, distance, _feature_edge_selection(edges, operation="chamfer")),
        )

    def shell(self, thickness, *, open=Faces.TOP):
        """Hollow a supported solid and leave selected Faces open.

        Parameters:
            thickness: Wall thickness in mm.
            open: Face to remove, or a non-empty sequence of Faces values. Defaults to Faces.TOP.

        Use when:
            Create an enclosure-like body with an even wall thickness while
            removing one or more named planar faces.

        Limits:
            open= must be one Faces value or a non-empty sequence of Faces
            values. Support still depends on the underlying feature tree.

        Example:
            Box(80, 50, 30).shell(2, open=Faces.TOP)
        """
        _pv(thickness)
        if isinstance(open, Faces):
            faces = (open,)
        elif isinstance(open, (list, tuple)) and open:
            try:
                faces = tuple(Faces(face) for face in open)
            except ValueError as exc:
                raise ValueError("shell open faces must use Faces values") from exc
        else:
            raise ValueError("shell open must be a Faces value or non-empty sequence")
        return Shape("shell", (self, thickness, faces))

    def with_material(self, name, *, density_g_cm3, color=None):
        """Assign one design-owned physical material to the final body."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("material name must be a non-empty string")
        if not isinstance(density_g_cm3, (int, float)) or not 0 < density_g_cm3 <= 1000:
            raise ValueError("material density must be in (0, 1000] g/cm3")
        if color is not None and (not isinstance(color, str) or
                                  len(color) != 7 or color[0] != "#" or
                                  any(c not in "0123456789abcdefABCDEF" for c in color[1:])):
            raise ValueError("material color must be a #RRGGBB hex string")
        return Shape("material_assignment", (self, name, density_g_cm3, color))

    def at(self, x=0, y=0, z=0, *, anchor=Anchor.CENTER, child=Anchor.CENTER):
        """Place a shape at absolute coordinates or align it to another Shape.

        Parameters:
            x: Absolute X coordinate in mm, or a target Shape for shape-to-shape alignment.
            y: Absolute Y coordinate in mm. Leave at 0 when x is a target Shape.
            z: Absolute Z coordinate in mm. Leave at 0 when x is a target Shape.
            anchor: Datum on this primitive that is placed at the requested coordinate. Defaults to Anchor.CENTER.
            child: Child datum for shape-to-shape alignment. Currently only Anchor.CENTER is supported.

        Use when:
            Use shape.at(x, y, z) for geometric placement. Box, Cylinder,
            Cone and Sphere support their documented anchors. Use shape.at(target) for the
            supported shape-to-shape CENTER alignment.

        Limits:
            Shape-to-shape alignment currently supports CENTER-to-CENTER only.
            at() is geometric placement/alignment; selecting a support face for
            a feature is the job of Shape.on().

        Example:
            pin = Cylinder(d=8, h=20, axis=Axis.X).at(10, 0, 5, anchor=Anchor.LEFT)
            centered = Sphere(5).at(body)
        """
        if isinstance(x, Shape):
            if y != 0 or z != 0:
                raise ValueError(
                    "at(target, ...) does not accept coordinate y/z arguments"
                )
            try:
                anchor = Anchor(anchor)
                child = Anchor(child)
            except ValueError as exc:
                raise ValueError("at() requires valid Anchor values") from exc
            if anchor is not Anchor.CENTER or child is not Anchor.CENTER:
                raise ValueError(
                    "shape-to-shape at() currently supports CENTER-to-CENTER only"
                )
            target_center = _shape_center(x)
            child_center = _shape_center(self)
            delta = tuple(
                _dim_sub(target_center[i], child_center[i])
                for i in range(3)
            )
            return Shape("translated", (self, delta))

        if self.kind == "box":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            selector = _direction_selector(anchor)
            return Shape("placed_box", (self, x, y, z, selector))

        if self.kind == "cylinder":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            height, diameter, axis, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            placed = Shape("cylinder", (height, diameter, axis, selected))
            return Shape("placed3d", (placed, x, y, z))

        if self.kind == "cone":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            height, diameter, top_diameter, axis, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            _cone_base_from_anchor(height, axis, (0, 0, 0), selected)
            placed = Shape(
                "cone",
                (height, diameter, top_diameter, axis, selected),
            )
            return Shape("placed3d", (placed, x, y, z))

        if self.kind == "sphere":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            radius, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            placed = Shape("sphere", (radius, selected))
            return Shape("translated", (placed, (x, y, z)))

        if anchor is not Anchor.CENTER or child is not Anchor.CENTER:
            raise ValueError(
                "anchor/child are only valid for geometric primitives or "
                "shape-to-shape at()"
            )
        if self.kind not in (
            "circle", "rectangle", "polygon", "positioned", "cylinder", "hole",
            "lip", "snap_fit", "boss", "rest",
        ):
            raise ValueError("at() does not support this shape")
        return Shape(
            "placed3d" if self.kind in (
                "cylinder", "hole", "lip", "snap_fit", "boss", "rest"
            ) else "positioned",
            (self, x, y, z),
        )

    def rectangular_pattern(
        self,
        feature,
        *,
        count,
        spacing,
        direction=Axis.X,
        count2=None,
        spacing2=None,
        direction2=Axis.Y,
        alignment="right",
        alignment2="right",
        reversed=False,
        reversed2=False,
    ):
        """Pattern an existing native history feature in one or two directions.

        Parameters:
            feature: Existing Sketch.extrude() feature already applied to this Shape, or a non-empty sequence of such features.
            count: Number of instances in the first direction. Use a positive integer or direct Parameter.
            spacing: Instance spacing in the first direction, in mm.
            direction: First pattern direction as Axis.X/Y/Z or a non-zero XYZ vector. Defaults to Axis.X.
            count2: Optional instance count for the second direction.
            spacing2: Optional spacing for the second direction, in mm.
            direction2: Second pattern direction as Axis.X/Y/Z or a non-zero XYZ vector. Defaults to Axis.Y.
            alignment: First-direction native alignment: "left", "center" or "right". Defaults to "right".
            alignment2: Second-direction native alignment: "left", "center" or "right". Defaults to "right".
            reversed: Reverse the first native pattern direction. Defaults to False.
            reversed2: Reverse the second native pattern direction. Defaults to False.

        Use when:
            Repeat an already-created native sketch extrusion while keeping one
            editable SolidCraft rectangular-pattern history feature.

        Limits:
            The source feature must already be part of this Shape. Supplying a
            second direction requires both count2 and spacing2.

        Example:
            plate.rectangular_pattern(cut, count=3, spacing=24, direction=Axis.X, count2=2, spacing2=28)
        """
        sources = _feature_pattern_sources(self, feature, "rectangular_pattern")

        count = _pattern_count(count, "rectangular_pattern count")
        if _pv(spacing) <= 0:
            raise ValueError("rectangular_pattern spacing must be positive")
        dir1 = _pattern_direction(direction, "rectangular_pattern direction")

        second_requested = count2 is not None or spacing2 is not None
        if second_requested and (count2 is None or spacing2 is None):
            raise ValueError(
                "rectangular_pattern second direction requires count2 and spacing2"
            )
        if second_requested:
            count2 = _pattern_count(count2, "rectangular_pattern count2")
            if _pv(spacing2) <= 0:
                raise ValueError("rectangular_pattern spacing2 must be positive")
            dir2 = _pattern_direction(direction2, "rectangular_pattern direction2")
        else:
            count2 = spacing2 = dir2 = None

        if alignment not in ("left", "center", "right"):
            raise ValueError("rectangular_pattern alignment must be left, center or right")
        if second_requested and alignment2 not in ("left", "center", "right"):
            raise ValueError("rectangular_pattern alignment2 must be left, center or right")
        if not isinstance(reversed, bool) or not isinstance(reversed2, bool):
            raise TypeError("rectangular_pattern reversed flags must be bool")

        return Shape(
            "rectangular_pattern",
            (
                self, sources,
                dir1, count, spacing,
                dir2, count2, spacing2,
                alignment, alignment2,
                reversed, reversed2,
            ),
        )

    def circular_pattern(
        self,
        feature,
        *,
        count,
        axis=Axis.Z,
        angle=None,
        origin=None,
        alignment="right",
        reversed=False,
    ):
        """Pattern an existing native history feature around a fixed axis.

        Parameters:
            feature: Existing Sketch.extrude() feature already applied to this Shape, or a non-empty sequence of such features.
            count: Total number of instances including the original. Use a positive integer or direct Parameter.
            axis: Rotation axis as Axis.X/Y/Z or a non-zero fixed XYZ direction. Defaults to Axis.Z.
            angle: Optional total pattern angle in degrees, as a fixed number or direct Parameter. Omit it for SolidCraft's native 360-degree default.
            origin: Optional XYZ point for a shifted fixed axis. With an Axis value and no origin, Forge emits the native principal-axis name directly.
            alignment: Native alignment: "left", "center" or "right". Defaults to "right".
            reversed: Reverse the native pattern direction. Defaults to False.

        Use when:
            Repeat an already-created native sketch extrusion around an axis
            while keeping one editable SolidCraft circular-pattern history
            feature, for example a bolt circle.

        Limits:
            The source feature must already be part of this Shape. Axis values
            cover principal or fixed XYZ axes. Native construction-axis,
            edge-axis and face-axis selectors are not exposed yet.

        Example:
            flange.circular_pattern(bolt_cut, count=6, axis=Axis.Z)
        """
        sources = _feature_pattern_sources(self, feature, "circular_pattern")
        count = _pattern_count(count, "circular_pattern count")
        axis_spec = _circular_pattern_axis(axis, origin)
        angle = _pattern_angle(angle, "circular_pattern angle")
        if alignment not in ("left", "center", "right"):
            raise ValueError(
                "circular_pattern alignment must be left, center or right"
            )
        if not isinstance(reversed, bool):
            raise TypeError("circular_pattern reversed must be bool")
        return Shape(
            "circular_pattern",
            (
                self,
                sources,
                axis_spec,
                count,
                angle,
                alignment,
                reversed,
            ),
        )

    def on(self, target, *, face=Faces.TOP, offset=(0, 0)):
        """Place a supported within-component feature on a target face.

        Parameters:
            target: Existing Shape that receives the feature.
            face: Target surface. Currently Faces.TOP or Faces.BOTTOM. Defaults to Faces.TOP.
            offset: In-plane (x, y) offset from the target face centre, in mm. Defaults to (0, 0).

        Use when:
            Put a Hole or another supported feature on an existing Shape and
            select its entry/support surface with Faces.

        Limits:
            Shape.on() currently accepts Faces.TOP and Faces.BOTTOM. This is
            feature placement; component assembly attachment uses Anchor and
            the component occurrence attach() API.

        Example:
            Hole(d=8).on(plate, face=Faces.TOP, offset=(20, 0))
        """
        try:
            face = Faces(face)
        except ValueError as exc:
            raise ValueError("on() face must be a Faces value") from exc
        face_to_anchor = {
            Faces.TOP: Anchor.TOP,
            Faces.BOTTOM: Anchor.BOTTOM,
        }
        if face not in face_to_anchor:
            raise ValueError("on() currently supports Faces.TOP or Faces.BOTTOM")
        return self._anchor_to(target, face_to_anchor[face], Anchor.BOTTOM, offset)

    def attach(self, target, *, parent=Anchor.TOP, child=Anchor.BOTTOM,
               offset=(0, 0)):
        """Anchor a supported feature explicitly to another Shape.

        Parameters:
            target: Existing parent Shape that receives the feature.
            parent: Anchor on the target Shape. Defaults to Anchor.TOP.
            child: Anchor on the feature being placed. Defaults to Anchor.BOTTOM.
            offset: In-plane (x, y) offset on the parent anchor surface, in mm. Defaults to (0, 0).

        Use when:
            Use this lower-level feature-placement form when parent/child
            Anchor references are required explicitly.

        Limits:
            This is legacy within-component feature anchoring. Prefer on() for
            simple face placement. It is separate from component occurrence
            attachment used by assemblies.

        Example:
            Boss(d=7, h=12).attach(case, parent=Anchor.INNER_BOTTOM, offset=(10, 10))
        """
        return self._anchor_to(target, parent, child, offset)

    def _anchor_to(self, target, parent_anchor, child_anchor, offset):
        if self.kind not in (
            "cylinder", "linear_repeat", "hole",
            "lip", "snap_fit", "boss", "rest",
        ):
            raise ValueError(
                "attach() supports Cylinder, Hole, plastic features and their supported patterns"
            )
        if not isinstance(target, Shape):
            raise TypeError("anchor target must be an existing Shape")
        try:
            parent_anchor = Anchor(parent_anchor)
            child_anchor = Anchor(child_anchor)
        except ValueError as exc:
            raise ValueError("unknown parent or child anchor") from exc
        if not isinstance(offset, (tuple, list)) or len(offset) != 2:
            raise ValueError("offset must be a pair (x, y)")
        for index, value in enumerate(offset):
            if isinstance(value, _BoundOffset):
                expected_axis = "X" if index == 0 else "Y"
                if value.axis != expected_axis:
                    raise ValueError(
                        f"offset position {index} requires {expected_axis} bounds"
                    )
                if not isfinite(_pv(value.delta)):
                    raise ValueError("bound offset must be finite")
            else:
                _pv(value)
        return Shape(
            "anchored",
            (self, target, parent_anchor, child_anchor, tuple(offset)),
        )

def _shape(value):
    if not isinstance(value, Shape):
        raise TypeError("boolean operations require a Shape")
    return value


def Text2D(text, *, height=6.0, font="DejaVu Sans Bold"):
    """Editable sketch lettering (height is capital height, in mm)."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text2D requires non-empty text")
    if not isinstance(font, str) or not font.strip():
        raise ValueError("Text2D requires a font family")
    if _pv(height) <= 0:
        raise ValueError("Text2D height must be positive")
    from .explicit_sketch import register_profile
    return register_profile(Shape("text", (text, height, font)))


def Rectangle2D(width, depth):
    """Create a rectangular 2D profile.

    Parameters:
        width: Rectangle size along the first local sketch axis, in mm. On XY this is X.
        depth: Rectangle size along the second local sketch axis, in mm. On XY this is Y.

    Use when:
        Author a simple rectangle inside an explicit Sketch before extrusion.

    Limits:
        The dimension-defined profile is centred on the Sketch origin by
        default. Use Sketch.add(..., offset=(u, v)) for a deliberate local
        displacement.

    Example:
        Rectangle2D(80, 50)
    """
    from .explicit_sketch import register_profile
    return register_profile(Shape("rectangle", (width, depth)))


def RoundedRectangle2D(width, depth, radius):
    """Create a native rounded-rectangle 2D profile.

    Parameters:
        width: Rectangle size along the first local sketch axis, in mm.
        depth: Rectangle size along the second local sketch axis, in mm.
        radius: Radius of each corner arc, in mm.

    Use when:
        A sketch needs a rectangle with true circular corner arcs rather than a
        polygonal approximation.

    Limits:
        Current support is inside an explicit Sketch. width and depth must be
        positive. radius must be positive and below half the shorter side.

    Example:
        RoundedRectangle2D(80, 50, 6)
    """
    if _pv(width) <= 0 or _pv(depth) <= 0:
        raise ValueError("RoundedRectangle2D width and depth must be positive")
    if not 0 < _pv(radius) * 2 < min(_pv(width), _pv(depth)):
        raise ValueError("RoundedRectangle2D radius must be below half the shorter side")
    from .explicit_sketch import register_profile
    return register_profile(Shape("rounded_rectangle", (width, depth, radius)))


def _slot_point(name, value):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{name} must be an (x, y) point")
    point = tuple(value)
    concrete = tuple(_pv(coordinate) for coordinate in point)
    if not all(isfinite(coordinate) for coordinate in concrete):
        raise ValueError(f"{name} must contain finite coordinates")
    # SolidCraft's native Slot creators take authored sketch points. Keep
    # those positions fixed; dimensions such as width remain symbolic.
    if any(isinstance(coordinate, (Parameter, Expression)) for coordinate in point):
        raise TypeError(f"{name} currently requires fixed numeric coordinates")
    return point


def _slot_width(width):
    # SolidCraft 0.42 accepts a number or expression for native Slot width.
    # Validate the current value without discarding the symbolic dependency.
    if isinstance(width, bool) or not isinstance(
        width,
        (int, float, Parameter, Expression),
    ):
        raise TypeError(
            "native Slot width must be a number, Parameter or Expression"
        )
    concrete = _pv(width)
    if not isfinite(concrete) or concrete <= 0:
        raise ValueError("slot width must be a positive finite number")
    return width


def SlotCenterToCenter2D(p0, p1, width):
    """Create a straight Slot from the centres of its two round ends.

    Parameters:
        p0: Centre of the first round end as (x, y) in sketch coordinates, in mm.
        p1: Centre of the second round end as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm. This is also the diameter of each round end.

    Limits:
        p0 and p1 must be different points. The straight part runs between
        these two end centres.

    Example:
        SlotCenterToCenter2D((-10, 0), (10, 0), 6)
    """
    p0 = _slot_point("p0", p0)
    p1 = _slot_point("p1", p1)
    if p0 == p1:
        raise ValueError("center-to-center Slot endpoints must differ")
    from .explicit_sketch import register_profile
    return register_profile(
        Shape("slot_center_to_center", (p0, p1, _slot_width(width)))
    )


def SlotOverall2D(p0, p1, width):
    """Create a straight Slot from its two outermost end points.

    Parameters:
        p0: Outermost point of the first round end as (x, y) in sketch coordinates, in mm.
        p1: Outermost point of the second round end as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm. This is also the diameter of each round end.

    Limits:
        The distance from p0 to p1 is the total Slot length, including both
        round ends, and must be larger than width.

    Example:
        SlotOverall2D((-15, 0), (15, 0), 6)
    """
    p0 = _slot_point("p0", p0)
    p1 = _slot_point("p1", p1)
    width = _slot_width(width)
    length = sum((b - a) ** 2 for a, b in zip(p0, p1)) ** 0.5
    if length <= _pv(width):
        raise ValueError("overall Slot length must be larger than its width")
    from .explicit_sketch import register_profile
    return register_profile(Shape("slot_overall", (p0, p1, width)))


def SlotCenterPoint2D(center, end, width):
    """Create a straight Slot from its centre and one round-end centre.

    Parameters:
        center: Centre of the complete Slot as (x, y) in sketch coordinates, in mm.
        end: Centre of one round end as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm. This is also the diameter of each round end.

    Limits:
        center and end must differ. The other round-end centre is mirrored
        through center.

    Example:
        SlotCenterPoint2D((0, 0), (10, 0), 6)
    """
    center = _slot_point("center", center)
    end = _slot_point("end", end)
    if center == end:
        raise ValueError("center-point Slot end must differ from its centre")
    from .explicit_sketch import register_profile
    return register_profile(
        Shape("slot_center_point", (center, end, _slot_width(width)))
    )


def SlotArcThreePoint2D(start, through, end, width):
    """Create a curved Slot whose centre arc passes through three points.

    Parameters:
        start: Start point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        through: A point that the centre arc must pass through, as (x, y) in mm.
        end: End point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm, measured perpendicular to the centre arc.

    Limits:
        start, through and end must be three different points.

    Example:
        SlotArcThreePoint2D((-15, 0), (0, 10), (15, 0), 6)
    """
    start = _slot_point("start", start)
    through = _slot_point("through", through)
    end = _slot_point("end", end)
    if len({start, through, end}) != 3:
        raise ValueError("three-point arc Slot requires three distinct points")
    from .explicit_sketch import register_profile
    return register_profile(
        Shape("slot_arc_three_point", (start, through, end, _slot_width(width)))
    )


def SlotArcCenter2D(center, start, width, *, end=None, sweep=None):
    """Create a curved Slot from an arc centre and start point.

    Parameters:
        center: Centre of the underlying circular arc as (x, y) in sketch coordinates, in mm.
        start: Start point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm, measured perpendicular to the centre arc.
        end: Optional end point of the centre arc as (x, y) in mm.
        sweep: Optional positive sweep angle in degrees.

    Limits:
        Supply exactly one of end= or sweep=. center and start must differ.
        sweep must be greater than 0 and less than 360 degrees.

    Example:
        SlotArcCenter2D((0, 0), (12, 0), 6, sweep=120)
    """
    center = _slot_point("center", center)
    start = _slot_point("start", start)
    if center == start:
        raise ValueError("arc Slot start must differ from its centre")
    if (end is None) == (sweep is None):
        raise ValueError("arc Slot requires exactly one of end= or sweep=")
    if end is not None:
        end = _slot_point("end", end)
    else:
        if isinstance(sweep, bool) or not isinstance(sweep, (int, float)):
            raise TypeError("arc Slot sweep must be a numeric angle in degrees")
        if not isfinite(sweep) or not 0 < sweep < 360:
            raise ValueError("arc Slot sweep must be between 0 and 360 degrees")
    from .explicit_sketch import register_profile
    return register_profile(
        Shape("slot_arc_center", (center, start, end, sweep, _slot_width(width)))
    )

def Circle2D(*, d=None, r=None):
    """Create a circular 2D profile by diameter or radius.

    Parameters:
        d: Circle diameter in mm. Supply d or r, not both.
        r: Circle radius in mm. Supply r or d, not both.

    Use when:
        Author a circular profile inside an explicit Sketch.

    Limits:
        Supply exactly one of d= or r=. The Sketch determines the plane.

    Example:
        Circle2D(d=8)
    """
    if (d is None) == (r is None):
        raise ValueError("Circle2D requires exactly one of d= or r=")
    from .explicit_sketch import register_profile
    return register_profile(Shape("circle", (d if d is not None else r * 2,)))


def Polygon2D(points, *, plane="XY", ids=None, world=False):
    """Create a closed named or unnamed polygon profile.

    Parameters:
        points: Polygon vertices in order. Use (u, v) pairs, or (name, (u, v)) pairs when naming vertices, in mm.
        plane: Sketch plane: "XY", "XZ" or "YZ". Defaults to "XY".
        ids: Optional segment names, one per polygon edge in vertex order.
        world: When True with plane="XZ", read each input point as world (x, z) instead of native sketch coordinates.

    Use when:
        A 2D profile needs arbitrary straight segments or named vertices and
        segments that later drive selectors such as Edges.from_profile().

    Limits:
        At least three 2D points are required. Named and unnamed points cannot
        be mixed. world=True currently supports only plane="XZ".

    Example:
        Polygon2D([(0, 0), (40, 0), (40, 20), (0, 20)], plane="XY")
    """
    rows = tuple(points)
    named = [
        isinstance(row, (tuple, list)) and len(row) == 2
        and isinstance(row[0], str) and isinstance(row[1], (tuple, list))
        for row in rows
    ]
    if any(named):
        if not all(named):
            raise ValueError("all polygon vertices must be named, or none")
        if ids is not None:
            raise ValueError("named polygon points cannot also specify ids")
        ids = tuple(row[0] for row in rows)
        coordinates = tuple(tuple(row[1]) for row in rows)
    else:
        coordinates = tuple(tuple(p) for p in rows)
    if len(coordinates) < 3 or any(len(p) != 2 for p in coordinates):
        raise ValueError("Polygon2D requires at least three 2D points")
    if plane not in ("XY", "XZ", "YZ"):
        raise ValueError("unsupported sketch plane")
    if world:
        if plane != "XZ":
            raise ValueError("world=True currently supports only plane='XZ'")
        coordinates = tuple((x, -z) for x, z in coordinates)
    if ids is not None:
        if isinstance(ids, (str, bytes)) or not isinstance(ids, (tuple, list)):
            raise ValueError("polygon ids must be a sequence of segment names")
        if len(ids) != len(coordinates):
            raise ValueError("closed polygon needs exactly one id per segment")
        if any(not isinstance(tag, str) or not tag or
               not tag[0].isalpha() or
               not all(c.isalnum() or c == "_" for c in tag)
               for tag in ids):
            raise ValueError("polygon ids must be non-empty alphanumeric identifiers")
        if len(set(ids)) != len(ids):
            raise ValueError("polygon ids must be unique")
        ids = tuple(ids)
    from .explicit_sketch import register_profile
    return register_profile(Shape("polygon", (coordinates, plane, ids)))


def Box(length, width, thickness, *, anchor=Anchor.CENTER):
    """Create a native rectangular solid around a declared anchor datum.

    Parameters:
        length: Box size along X, in mm.
        width: Box size along Y, in mm.
        thickness: Box size along Z, in mm.
        anchor: Box datum placed at model coordinate (0, 0, 0) before later placement. Defaults to Anchor.CENTER.

    Use when:
        Model a simple rectangular part directly without introducing a Sketch.

    Limits:
        The default anchor is CENTER, so an unplaced Box is centred around the
        model origin in X, Y and Z. Use anchor=BOTTOM for a box whose bottom
        face centre is at Z=0. Use at() for later placement.

    Example:
        Box(80, 50, 12, anchor=Anchor.BOTTOM)
    """
    selector = _direction_selector(anchor)
    return Shape("box", (length, width, thickness, selector))


def Sphere(radius, *, anchor=Anchor.CENTER):
    """Create a sphere centred on the origin unless another anchor is given.

    Parameters:
        radius: Sphere radius in mm.
        anchor: Sphere datum placed at model coordinate (0, 0, 0) before later placement. Defaults to Anchor.CENTER.

    Use when:
        Model a spherical primitive, optionally with a tangent-point anchor.

    Limits:
        Cardinal anchors select points on the sphere's world-aligned bounds.
        Sphere has no separate orientation axis; use at() for placement.

    Example:
        Sphere(12, anchor=Anchor.BOTTOM)
    """
    return Shape("sphere", (radius, _direction_selector(anchor)))


def Cylinder(*, d, h, axis=Axis.Z, anchor=Anchor.CENTER):
    """Create a cylindrical solid centred around the origin by default.

    Parameters:
        d: Cylinder diameter in mm.
        h: Cylinder length along the selected axis, in mm.
        axis: Cylinder axis. Use Axis.X, Axis.Y or Axis.Z. Defaults to Axis.Z.
        anchor: Cylinder datum placed at model coordinate (0, 0, 0) before later placement. Defaults to Anchor.CENTER.

    Use when:
        Model a cylinder along Axis.X, Axis.Y or Axis.Z. Use BOTTOM for a
        Z-axis base, LEFT for an X-axis base or FRONT for a Y-axis base.

    Limits:
        Anchors refer to world XYZ bounds after choosing the cylinder axis.
        at() places the selected anchor at the requested coordinate.

    Example:
        Cylinder(d=8, h=20, axis=Axis.X, anchor=Anchor.LEFT)
    """
    try:
        axis = Axis(axis)
    except ValueError as exc:
        raise ValueError("Cylinder axis must be Axis.X, Axis.Y or Axis.Z") from exc
    return Shape("cylinder", (h, d, axis.value, _direction_selector(anchor)))


def Cone(*, d, top_d=0, h, axis=Axis.Z, anchor=Anchor.CENTER):
    """Create a native cone or tapered cylinder (frustum).

    Parameters:
        d: Diameter at the base end, in mm.
        top_d: Diameter at the other end, in mm. Defaults to 0 for a full cone.
        h: Length along the selected axis, in mm.
        axis: Cone axis. Use Axis.X, Axis.Y or Axis.Z. Defaults to Axis.Z.
        anchor: CENTER or one of the two axial end datums.

    Use when:
        Model a cone, tapered pin or lightly conical cylinder directly with
        SolidCraft's native solid.cone feature.

    Limits:
        Because the two end radii may differ, transverse tangent anchors are
        intentionally not exposed. Use CENTER or the selected axis' two end
        anchors: LEFT/RIGHT for X, FRONT/BACK for Y, BOTTOM/TOP for Z.

    Example:
        Cone(d=20, top_d=20.2, h=20, anchor=Anchor.BOTTOM)
    """
    try:
        axis = Axis(axis)
    except ValueError as exc:
        raise ValueError("Cone axis must be Axis.X, Axis.Y or Axis.Z") from exc
    selector = _direction_selector(anchor)
    _cone_base_from_anchor(h, axis.value, (0, 0, 0), selector)
    return Shape("cone", (h, d, top_d, axis.value, selector))


_HOLE_FIELDS = (
    "type",
    "diameter",
    "depth",
    "direction",
    "counterbore_diameter",
    "counterbore_depth",
    "countersink_diameter",
    "countersink_angle",
    "thread",
    "hand",
    "thread_depth",
    "modeled",
    "ease_out",
)


def _hole_spec(feature):
    """Return Hole-family data by meaning instead of tuple position."""
    if not isinstance(feature, Shape) or feature.kind != "hole":
        raise TypeError("expected Hole-family feature")
    return dict(zip(_HOLE_FIELDS, feature.data))


def _validate_hole_direction(direction):
    if direction is None:
        return None
    direction = tuple(direction)
    if len(direction) != 3:
        raise ValueError("Hole direction must be a 3D direction")
    concrete = [_pv(v) for v in direction]
    if not all(isfinite(v) for v in concrete) or concrete == [0, 0, 0]:
        raise ValueError("Hole direction must be a finite non-zero direction")
    return direction


def _hole_feature(
    hole_type,
    *,
    d=None,
    depth=Depth.THROUGH_ALL,
    direction=None,
    counterbore_d=None,
    counterbore_depth=None,
    countersink_d=None,
    countersink_angle=None,
    thread=None,
    hand="right",
    thread_depth=None,
    modeled=False,
    ease_out=None,
):
    """Build one validated native Hole-family feature description."""
    if d is not None and _pv(d) <= 0:
        raise ValueError("hole diameter must be positive")
    if depth is not Depth.THROUGH_ALL and _pv(depth) <= 0:
        raise ValueError("hole depth must be positive or Depth.THROUGH_ALL")
    direction = _validate_hole_direction(direction)

    if hole_type == "simple":
        if d is None:
            raise ValueError("Hole requires d")
    elif hole_type == "counterbore":
        if d is None:
            raise ValueError("CounterboreHole requires d")
        if counterbore_d is None or counterbore_depth is None:
            raise ValueError(
                "CounterboreHole requires counterbore_d and counterbore_depth"
            )
        if _pv(counterbore_d) <= _pv(d):
            raise ValueError(
                "counterbore diameter must be larger than hole diameter"
            )
        if _pv(counterbore_depth) <= 0:
            raise ValueError("counterbore depth must be positive")
    elif hole_type == "countersink":
        if d is None:
            raise ValueError("CountersinkHole requires d")
        if countersink_d is None:
            raise ValueError("CountersinkHole requires countersink_d")
        if _pv(countersink_d) <= _pv(d):
            raise ValueError(
                "countersink diameter must be larger than hole diameter"
            )
        angle = _pv(countersink_angle)
        if not isfinite(angle) or angle <= 0 or angle >= 180:
            raise ValueError(
                "countersink angle must be between 0 and 180 degrees"
            )
    elif hole_type == "threaded":
        if not isinstance(thread, str) or not thread.strip():
            raise ValueError("ThreadedHole requires a thread designation")
        if hand not in ("right", "left"):
            raise ValueError("thread hand must be 'right' or 'left'")
        if thread_depth is not None and _pv(thread_depth) <= 0:
            raise ValueError("thread depth must be positive")
        if ease_out is not None:
            if isinstance(ease_out, str):
                if ease_out not in ("standard", "short"):
                    raise ValueError(
                        "thread ease_out must be 'standard', 'short', or a positive length"
                    )
            elif _pv(ease_out) <= 0:
                raise ValueError("thread ease_out length must be positive")
        modeled = bool(modeled)
    else:
        raise ValueError(f"unsupported hole type: {hole_type}")

    return Shape(
        "hole",
        (
            hole_type,
            d,
            depth,
            direction,
            counterbore_d,
            counterbore_depth,
            countersink_d,
            countersink_angle,
            thread,
            hand,
            thread_depth,
            modeled,
            ease_out,
        ),
    )


def Hole(*, d, depth=Depth.THROUGH_ALL, direction=None):
    """Create a simple cylindrical hole feature.

    Parameters:
        d: Finished hole diameter in mm.
        depth: Hole depth in mm, or Depth.THROUGH_ALL. Defaults to through all.
        direction: Optional non-zero XYZ direction vector from the entry point into the material.

    Use when:
        Make an ordinary drilled hole without a head recess or thread intent.

    Limits:
        d and finite depth values must be positive. Explicit native Hole
        features are positioned with at(); face-relative repeated simple holes
        may also use on() through the existing placement route.

    Example:
        Hole(d=4.3).at(0, 0, 2)
    """
    return _hole_feature(
        "simple",
        d=d,
        depth=depth,
        direction=direction,
    )


def CounterboreHole(
    *,
    d,
    counterbore_d,
    counterbore_depth,
    depth=Depth.THROUGH_ALL,
    direction=None,
):
    """Create a hole with a cylindrical recess at its entry face.

    Parameters:
        d: Finished main-hole diameter in mm.
        counterbore_d: Diameter of the cylindrical recess in mm.
        counterbore_depth: Depth of the recess from the entry face in mm.
        depth: Main-hole depth in mm, or Depth.THROUGH_ALL. Defaults to through all.
        direction: Optional non-zero XYZ direction vector from the entry point into the material.

    Use when:
        Seat a cylindrical screw head or other part below the entry surface.

    Limits:
        counterbore_d must be larger than d. counterbore_depth and finite
        depth values must be positive. Position this native feature with at().

    Example:
        CounterboreHole(
            d=6,
            counterbore_d=12,
            counterbore_depth=4,
        ).at(0, 0, 12)
    """
    return _hole_feature(
        "counterbore",
        d=d,
        depth=depth,
        direction=direction,
        counterbore_d=counterbore_d,
        counterbore_depth=counterbore_depth,
    )


def CountersinkHole(
    *,
    d,
    countersink_d,
    countersink_angle=90,
    depth=Depth.THROUGH_ALL,
    direction=None,
):
    """Create a hole with a conical countersink at its entry face.

    Parameters:
        d: Finished main-hole diameter in mm.
        countersink_d: Diameter of the countersink at the entry face in mm.
        countersink_angle: Included countersink angle in degrees. Defaults to 90.
        depth: Main-hole depth in mm, or Depth.THROUGH_ALL. Defaults to through all.
        direction: Optional non-zero XYZ direction vector from the entry point into the material.

    Use when:
        Seat a countersunk fastener or specify a hole whose conical entry is
        part of the hole feature itself.

    Limits:
        countersink_d must be larger than d. countersink_angle must be between
        0 and 180 degrees. Position this native feature with at().

    Example:
        CountersinkHole(
            d=6,
            countersink_d=12,
            countersink_angle=90,
        ).at(0, 0, 12)
    """
    return _hole_feature(
        "countersink",
        d=d,
        depth=depth,
        direction=direction,
        countersink_d=countersink_d,
        countersink_angle=countersink_angle,
    )


def ThreadedHole(
    *,
    thread,
    depth=Depth.THROUGH_ALL,
    d=None,
    direction=None,
    hand="right",
    thread_depth=None,
    modeled=False,
    ease_out=None,
):
    """Create a tapped hole with native thread intent.

    Parameters:
        thread: Thread designation such as "M6" or "1/4-20 UNC".
        depth: Drill depth in mm, or Depth.THROUGH_ALL. Defaults to through all.
        d: Optional explicit tap-drill diameter in mm. When omitted, SolidCraft selects the drill from the thread designation.
        direction: Optional non-zero XYZ direction vector from the entry point into the material.
        hand: Thread hand, "right" or "left". Defaults to "right".
        thread_depth: Optional positive threaded length in mm, independent of drill depth.
        modeled: Whether SolidCraft cuts modeled thread geometry. Defaults to False.
        ease_out: Optional modeled-thread runout: "standard", "short", or a positive length.

    Use when:
        Preserve tapped-hole manufacturing intent instead of representing the
        result as an ordinary cylindrical subtraction.

    Limits:
        The thread designation must be supported by SolidCraft. modeled=True
        creates actual thread geometry and can be substantially heavier than
        cosmetic/native thread metadata. Position this native feature with at().

    Example:
        ThreadedHole(
            thread="M6",
            d=5,
            thread_depth=10,
            modeled=True,
        ).at(0, 0, 12)
    """
    return _hole_feature(
        "threaded",
        d=d,
        depth=depth,
        direction=direction,
        thread=thread,
        hand=hand,
        thread_depth=thread_depth,
        modeled=modeled,
        ease_out=ease_out,
    )


def Lip(*, width, height):
    """Create a plastic enclosure lip feature.

    Parameters:
        width: Lip width in mm.
        height: Lip height in mm.

    Use when:
        Add a lip to a supported shelled enclosure rim using feature placement.

    Limits:
        width and height must be positive when compiled. Placement and
        parent-shape support follow the feature-placement API.

    Example:
        Lip(width=2, height=3)
    """
    return Shape("lip", (width, height))


def SnapFit(*, length, thickness, width, catch_depth, catch_length,
            hook, direction=None):
    """Create a cantilever snap-fit feature.

    Parameters:
        length: Cantilever length in mm.
        thickness: Cantilever thickness in mm.
        width: Cantilever width in mm.
        catch_depth: Catch projection depth in mm.
        catch_length: Catch length in mm.
        hook: Non-zero XYZ direction vector for the hook direction.
        direction: Optional non-zero XYZ direction vector for the feature direction.

    Use when:
        Add a plastic snap feature to a supported face with an explicit hook
        direction.

    Limits:
        All five dimensions must be positive when compiled. hook must contain
        three coordinates; direction, when supplied, must also contain three.

    Example:
        SnapFit(length=20, thickness=2, width=8, catch_depth=1.5, catch_length=4, hook=(1, 0, 0))
    """
    hook = tuple(hook)
    if len(hook) != 3:
        raise ValueError("SnapFit hook must be a 3D direction")
    if direction is not None:
        direction = tuple(direction)
        if len(direction) != 3:
            raise ValueError("SnapFit direction must be a 3D direction")
    return Shape(
        "snap_fit",
        (length, thickness, width, catch_depth, catch_length, hook, direction),
    )


def Boss(*, d, h, hole_d=None, direction=None):
    """Create a plastic screw-boss feature.

    Parameters:
        d: Boss outside diameter in mm.
        h: Boss height in mm.
        hole_d: Optional central-hole diameter in mm.
        direction: Optional non-zero XYZ direction vector for the boss axis.

    Use when:
        Add a cylindrical support boss, optionally with a central hole, to a
        supported face.

    Limits:
        d and h must be positive when compiled. hole_d, when supplied, must be
        positive. direction, when supplied, must contain three coordinates.

    Example:
        Boss(d=7, h=12, hole_d=2.5)
    """
    if direction is not None:
        direction = tuple(direction)
        if len(direction) != 3:
            raise ValueError("Boss direction must be a 3D direction")
    return Shape(
        "boss",
        (d, h, hole_d, direction),
    )


def Rest(*, width, height, length=None, along=None, direction=None):
    """Create a plastic support/rest feature.

    Parameters:
        width: Rest width in mm.
        height: Rest height in mm.
        length: Optional rest length in mm for an elongated support.
        along: Optional non-zero XYZ vector that sets the long direction.
        direction: Optional non-zero XYZ vector that sets the feature direction.

    Use when:
        Add a support pad or elongated rest to a supported face.

    Limits:
        width and height must be positive when compiled. length, when supplied,
        must be positive. along and direction must contain three coordinates.

    Example:
        Rest(width=12, height=4, length=30, along=(1, 0, 0))
    """
    if along is not None:
        along = tuple(along)
        if len(along) != 3:
            raise ValueError("Rest along must be a 3D direction")
    if direction is not None:
        direction = tuple(direction)
        if len(direction) != 3:
            raise ValueError("Rest direction must be a 3D direction")
    return Shape("rest", (width, height, length, along, direction))


X, Y, Z = _AxisRef("X"), _AxisRef("Y"), _AxisRef("Z")

# BOSL2-style cardinal direction constants. These remain the same Anchor
# values used by assemblies, but can also be added to form edge/corner
# selectors such as BOTTOM + LEFT or TOP + RIGHT.
CENTER = Anchor.CENTER
TOP = Anchor.TOP
BOTTOM = Anchor.BOTTOM
LEFT = Anchor.LEFT
RIGHT = Anchor.RIGHT
FRONT = Anchor.FRONT
BACK = Anchor.BACK
UP = TOP
DOWN = BOTTOM
