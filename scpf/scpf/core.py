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


class Direction(str, Enum):
    """Choose how an extrusion extends relative to its sketch-plane normal.

    Use when:
        Pass a Direction to Sketch.extrude() when the default positive
        extrusion is not the intended direction.

    Limits:
        Direction describes extrusion relative to the sketch plane; it is not
        a world-axis selector. Use Axis for principal X/Y/Z directions.
    """
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SYMMETRIC = "symmetric"


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

    Use when:
        A standard face or corner Anchor is not enough and the mounting datum
        needs its own local origin plus orientation. A reusable component may
        expose named AnchorFrame values from anchors(), or an assembly may pass
        one directly to attach().

    Limits:
        origin is component-local. z is the attachment normal and x fixes the
        clocking around that normal; both directions must be non-zero and not
        parallel. Direct frames on explicitly rotated occurrences have limited
        support as documented by the assembly guide.
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

    Use when:
        A relationship should follow a particular edge, adjacent planar face
        and optionally one endpoint as dimensions change, rather than freezing
        one XYZ coordinate.

    Limits:
        edge and on are native selection pick points; corner is optional. z and
        x may override frame orientation. Current Forge support focuses on
        planar-face edges and non-rotated occurrences.
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

    Use when:
        Keep a value symbolic so generated SolidCraft commands can retain an
        editable dependency instead of baking in the current Python number.

    Limits:
        Names must be valid Python identifiers and values finite numbers.
        Normal public lower-case model fields are usually promoted to
        parameters automatically, so explicit Parameter() is mainly useful in
        lower-level or assembly code.
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

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.TOP, distance)


def down(distance):
    """Return a symbolic-safe XYZ offset in the -Z direction.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.BOTTOM, distance)


def left(distance):
    """Return a symbolic-safe XYZ offset in the -X direction.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.LEFT, distance)


def right(distance):
    """Return a symbolic-safe XYZ offset in the +X direction.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.RIGHT, distance)


def front(distance):
    """Return a symbolic-safe XYZ offset in the -Y direction.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.FRONT, distance)


def back(distance):
    """Return a symbolic-safe XYZ offset in the +Y direction.

    Use when:
        Express a readable placement offset while preserving Parameter or
        Expression values.

    Limits:
        This returns an XYZ tuple; it does not create an Anchor relationship.
    """
    return _scaled_direction(Anchor.BACK, distance)


def half(value):
    """Return half of a numeric or symbolic CAD dimension.

    Use when:
        Keep midpoint-style arithmetic readable without converting a symbolic
        CAD dimension to a concrete Python value.

    Limits:
        Equivalent to value / 2; the input must support that operation.
    """
    return value / 2


def midpoint(start, end):
    """Return the midpoint between two numeric or symbolic dimensions.

    Use when:
        Express a centre position while preserving symbolic CAD dependencies.

    Limits:
        Equivalent to (start + end) / 2; inputs must support symbolic arithmetic.
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

    Use when:
        Python itself genuinely needs a number for validation or control flow.

    Limits:
        Calling pv() intentionally removes the symbolic dependency at that
        point. Geometry and placement should normally keep Parameter/Expression
        objects symbolic so SolidCraft remains editable and associative.
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
        "CENTER alignment currently supports direct Box, Sphere, Cylinder "
        "and centered CSG composites"
    )


@dataclass(frozen=True)
class Shape:
    """Represent Forge geometry/feature intent before SolidCraft executes it.

    Use when:
        Shape values are normally returned by constructors such as Box(),
        Cylinder(), Hole() and Sketch.extrude(), then transformed or combined
        with the supported Shape methods/operators.

    Limits:
        Shape is Forge's model-intent node, not a second geometry kernel.
        SolidCraft owns the final BRep and native feature history; users normally
        do not instantiate Shape(kind, data) directly.
    """

    kind: str
    data: Any

    def __and__(self, other):
        return Shape("intersection", (self, _shape(other)))

    def __add__(self, other):
        return Shape("union", (self, _shape(other)))

    def __or__(self, other):
        return self + other

    def __sub__(self, other):
        return Shape("difference", (self, _shape(other)))

    def move(self, x=0, y=0, z=0):
        """Translate a CSG shape by millimetres.

        Translates all primitives in a composite CSG model together.
        General feature-based box placement is not implemented yet.
        """
        offsets = (_pv(x), _pv(y), _pv(z))
        if not all(isfinite(v) for v in offsets):
            raise ValueError("move() requires finite coordinates")
        if self.kind in ("fillet", "shell", "pattern"):
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

    def fillet(self, radius, *, edges=Edges.VERTICAL):
        if edges is Edges.VERTICAL or isinstance(edges, _ProfileEdgeSelection):
            return Shape("fillet", (self, radius, edges))

        directional = (
            isinstance(edges, (_DirectionSelector, Anchor))
            or (
                isinstance(edges, (list, tuple))
                and edges
                and all(isinstance(edge, (_DirectionSelector, Anchor)) for edge in edges)
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
                    "a Box edge selector must combine exactly two cardinal directions"
                )
            return Shape("fillet", (self, radius, selectors))

        if not isinstance(edges, (list, tuple)) or not edges:
            raise ValueError(
                "fillet edges must be directional selectors, Edges.VERTICAL "
                "or 3D edge points"
            )
        for point in edges:
            if len(point) != 3:
                raise ValueError("each fillet edge point must have x, y and z")
        return Shape("fillet", (self, radius, edges))

    def chamfer(self, distance, *, edges):
        """Chamfer explicitly selected solid edges by an equal distance."""
        _pv(distance)
        if isinstance(edges, _ProfileEdgeSelection):
            return Shape("chamfer", (self, distance, edges))
        if not isinstance(edges, (list, tuple)) or not edges:
            raise ValueError("chamfer edges must be a non-empty sequence of 3D edge points")
        for point in edges:
            if not isinstance(point, (list, tuple)) or len(point) != 3:
                raise ValueError("each chamfer edge point must have x, y and z")
            for coordinate in point:
                _pv(coordinate)
        return Shape("chamfer", (self, distance, tuple(tuple(p) for p in edges)))

    def shell(self, thickness, *, open=Faces.TOP):
        """Hollow a supported solid and leave selected Faces open.

        Use when:
            Create an enclosure-like body with an even wall thickness while
            removing one or more named planar faces.

        Limits:
            open= must be one Faces value or a non-empty sequence of Faces
            values. Support still depends on the underlying feature tree.
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

        Use when:
            Use shape.at(x, y, z) for geometric placement. A Box may additionally
            use a cardinal anchor. Use shape.at(target) for the supported
            shape-to-shape CENTER alignment.

        Limits:
            Shape-to-shape alignment currently supports CENTER-to-CENTER only.
            at() is geometric placement/alignment; selecting a support face for
            a feature is the job of Shape.on().
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

    def pattern(self, *, count, spacing, axis):
        """Repeat a Hole or Cylinder at symmetric offsets along an XY axis."""
        if self.kind not in ("cylinder", "hole"):
            raise ValueError("pattern() supports Cylinder or Hole")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("pattern count must be a positive integer")
        if _pv(spacing) <= 0:
            raise ValueError("pattern spacing must be positive")
        try:
            axis = Axis(axis)
        except ValueError as exc:
            raise ValueError("pattern axis must be Axis.X or Axis.Y") from exc
        if axis not in (Axis.X, Axis.Y):
            raise ValueError("only XY linear patterns are supported")
        return Shape("linear_pattern", (self, count, spacing, axis))

    def on(self, target, *, face=Faces.TOP, offset=(0, 0)):
        """Place a supported within-component feature on a target face.

        Use when:
            Put a Hole or another supported feature on an existing Shape and
            select its entry/support surface with Faces.

        Limits:
            Shape.on() currently accepts Faces.TOP and Faces.BOTTOM. This is
            feature placement; component assembly attachment uses Anchor and
            the component occurrence attach() API.
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

        Use when:
            Use this lower-level feature-placement form when parent/child
            Anchor references are required explicitly.

        Limits:
            This is legacy within-component feature anchoring. Prefer on() for
            simple face placement. It is separate from component occurrence
            attachment used by assemblies.
        """
        return self._anchor_to(target, parent, child, offset)

    def _anchor_to(self, target, parent_anchor, child_anchor, offset):
        if self.kind not in (
            "cylinder", "linear_pattern", "hole",
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

    Use when:
        Author a simple rectangle inside an explicit Sketch before extrusion.

    Limits:
        The dimension-defined profile is centred on the Sketch origin by
        default. Use Sketch.add(..., offset=(u, v)) for a deliberate local
        displacement.
    """
    from .explicit_sketch import register_profile
    return register_profile(Shape("rectangle", (width, depth)))


def RoundedRectangle2D(width, depth, radius):
    """Create a native rounded-rectangle 2D profile.

    Use when:
        A sketch needs a rectangle with true circular corner arcs rather than a
        polygonal approximation.

    Limits:
        Current support is inside an explicit Sketch. The radius must be below
        half the shorter side.
    """
    if _pv(width) <= 0 or _pv(depth) <= 0:
        raise ValueError("RoundedRectangle2D width and depth must be positive")
    if not 0 < _pv(radius) * 2 < min(_pv(width), _pv(depth)):
        raise ValueError("RoundedRectangle2D radius must be below half the shorter side")
    from .explicit_sketch import register_profile
    return register_profile(Shape("rounded_rectangle", (width, depth, radius)))


def Circle2D(*, d=None, r=None):
    """Create a circular 2D profile by diameter or radius.

    Use when:
        Author a circular profile inside an explicit Sketch.

    Limits:
        Supply exactly one of d= or r=; the Sketch determines the plane.
    """
    if (d is None) == (r is None):
        raise ValueError("Circle2D requires exactly one of d= or r=")
    from .explicit_sketch import register_profile
    return register_profile(Shape("circle", (d if d is not None else r * 2,)))


def Polygon2D(points, *, plane="XY", ids=None, world=False):
    """Create a closed named or unnamed polygon profile.

    Use when:
        A 2D profile needs arbitrary straight segments or named vertices and
        segments that later drive selectors such as Edges.from_profile().

    Limits:
        At least three 2D points are required. plane is XY, XZ or YZ.
        world=True currently supports only XZ and lets input use intuitive
        world (x, z) coordinates.
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

    Use when:
        Model a simple rectangular part directly without introducing a Sketch.
        anchor selects which Box anchor starts at model coordinate (0, 0, 0).

    Limits:
        The default anchor is CENTER, so an unplaced Box is centred around the
        model origin in X, Y and Z. Use anchor=BOTTOM for a box whose bottom
        face centre is at Z=0. Use at() for later placement.
    """
    selector = _direction_selector(anchor)
    return Shape("box", (length, width, thickness, selector))


def Sphere(radius, *, anchor=Anchor.CENTER):
    """Create a sphere, centered on the origin unless another anchor is given.

    Use when:
        Model a spherical primitive, optionally with a tangent-point anchor.

    Limits:
        Cardinal anchors select points on the sphere's world-aligned bounds.
        Sphere has no separate orientation axis; use at() for placement.
    """
    return Shape("sphere", (radius, _direction_selector(anchor)))


def Cylinder(*, d, h, axis=Axis.Z, anchor=Anchor.CENTER):
    """Create a cylindrical solid centered around the origin by default.

    Use when:
        Model a cylinder along Axis.X, Axis.Y or Axis.Z. Use BOTTOM for a
        Z-axis base, LEFT for an X-axis base or FRONT for a Y-axis base.

    Limits:
        Anchors refer to world XYZ bounds after choosing the cylinder axis.
        at() places the selected anchor at the requested coordinate.
    """
    try:
        axis = Axis(axis)
    except ValueError as exc:
        raise ValueError("Cylinder axis must be Axis.X, Axis.Y or Axis.Z") from exc
    return Shape("cylinder", (h, d, axis.value, _direction_selector(anchor)))


def Hole(*, d, depth=Depth.THROUGH_ALL, direction=None,
         countersink_d=None, countersink_angle=90, countersink_recess=0):
    """Create hole feature intent, optionally directional and countersunk.

    Use when:
        Remove a manufacturing-style hole from a supported body. Simple holes
        can be placed with on(); directional or countersunk holes can use the
        native Hole path with explicit placement.

    Limits:
        Diameter must be positive. depth is a positive distance or
        Depth.THROUGH_ALL. Countersink diameter must exceed the hole diameter.
    """
    if _pv(d) <= 0:
        raise ValueError("hole diameter must be positive")
    if depth is not Depth.THROUGH_ALL and _pv(depth) <= 0:
        raise ValueError("hole depth must be positive or Depth.THROUGH_ALL")
    if direction is not None:
        direction = tuple(direction)
        if len(direction) != 3:
            raise ValueError("Hole direction must be a 3D direction")
        concrete = [_pv(v) for v in direction]
        if not all(isfinite(v) for v in concrete) or concrete == [0, 0, 0]:
            raise ValueError("Hole direction must be a finite non-zero direction")
    if countersink_d is not None:
        if _pv(countersink_d) <= _pv(d):
            raise ValueError("countersink diameter must be larger than hole diameter")
        angle = _pv(countersink_angle)
        if not isfinite(angle) or angle <= 0 or angle >= 180:
            raise ValueError("countersink angle must be between 0 and 180 degrees")
        if _pv(countersink_recess) < 0:
            raise ValueError("countersink recess cannot be negative")
    elif _pv(countersink_recess) != 0:
        raise ValueError("countersink recess requires countersink_d")
    return Shape(
        "hole",
        (
            d, depth, direction, countersink_d, countersink_angle,
            countersink_recess,
        ),
    )


def Lip(*, width, height):
    """Create plastic enclosure lip feature intent.

    Use when:
        Add a lip to a supported shelled enclosure rim using feature placement.

    Limits:
        Placement and parent-shape support follow the feature-placement API.
    """
    return Shape("lip", (width, height))


def SnapFit(*, length, thickness, width, catch_depth, catch_length,
            hook, direction=None):
    """Create cantilever snap-fit feature intent.

    Use when:
        Add a plastic snap feature to a supported face with an explicit hook
        direction.

    Limits:
        hook must be one 3D direction; optional direction must also be an XYZ
        triple. Placement uses the supported feature-placement API.
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
    """Create plastic screw-boss feature intent.

    Use when:
        Add a cylindrical support boss, optionally with a central hole, to a
        supported face.

    Limits:
        Optional direction is an XYZ triple. Boss intent lowers through the
        native plastic.boss feature path; use Sketch explicitly when sketch
        history is part of the design intent.
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
    """Create plastic support/rest feature intent.

    Use when:
        Add a support pad or elongated rest to a supported face.

    Limits:
        Optional along and direction values are XYZ triples. Placement uses the
        supported feature-placement API.
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
