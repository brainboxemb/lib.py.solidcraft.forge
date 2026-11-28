"""Anchors, directions, axes and topology-selection authoring."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

from .scalars import Parameter, Expression, _pv

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
    """Select topology for supported edge-consuming feature operations.

    Use when:
        Use from_faces() to select the complete boundary of one or more
        cardinal Faces through native SolidCraft topology. Edges.VERTICAL,
        from_profile() and from_vertices() remain available for their existing
        source-compatible selection contracts.

    Limits:
        from_faces() selects boundaries of the largest planar face matching
        each requested cardinal direction. from_profile() currently supports
        sides="both"; from_vertices() requires named Polygon2D vertices.
    """
    VERTICAL = "vertical"

    @staticmethod
    def from_faces(*faces):
        """Select all native boundary edges of one or more cardinal Faces.

        Forge resolves each face and its boundary from SolidCraft at replay
        time. Callers do not provide or predict native topology ids.
        """
        if not faces:
            raise ValueError("provide one or more Faces values")
        try:
            normalized = tuple(Faces(face) for face in faces)
        except ValueError as exc:
            raise ValueError("from_faces() requires Faces values") from exc
        return _FaceBoundarySelection(normalized)

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

@dataclass(frozen=True)
class _ProfileEdgeSelection:
    patterns: tuple[str, ...]
    sides: str
    kind: str = "segments"

def _feature_edge_selection(edges, *, operation):
    """Validate one public fillet/chamfer edge selection."""
    if edges is Edges.VERTICAL or isinstance(
        edges, (_ProfileEdgeSelection, _FaceBoundarySelection)
    ):
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
    """Select cardinal planar surfaces consistently across feature operations.

    Use when:
        Pass a Faces value to Shape.on(), Shape.shell() or Edges.from_faces()
        so placement and modify features share one surface vocabulary.

    Limits:
        TOP/BOTTOM are +/-Z, LEFT/RIGHT are -/+X and FRONT/BACK are -/+Y.
        Native lowering selects the largest planar face with that normal when
        topology inspection is used. Component assembly attachment uses Anchor.
    """
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"


@dataclass(frozen=True)

@dataclass(frozen=True)
class _FaceBoundarySelection:
    """Internal request for native boundary edges of cardinal Faces."""

    faces: tuple[Faces, ...]


@dataclass(frozen=True)

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


@dataclass(frozen=True)

@dataclass(frozen=True)
class AxisLine:
    """Describe one fixed-direction native axis through an explicit XYZ origin.

    Parameters:
        direction: Axis.X/Y/Z or one non-zero fixed XYZ direction.
        origin: XYZ point on the axis. Coordinates may be Parameter/Expression.

    Use when:
        A native feature needs a shifted/custom axis while retaining editable
        model-parameter dependencies, for example an offset revolve or circular
        pattern.

    Limits:
        Direction is fixed authored orientation; symbolic direction vectors are
        not supported. Feature-specific APIs still validate whether the line is
        geometrically valid for their sketch/profile.

    Example:
        axis = AxisLine(Axis.Y, origin=(pin_x, 0, pin_z))
    """

    direction: object
    origin: tuple[object, object, object] = (0, 0, 0)

    def __post_init__(self):
        direction = _pattern_direction(self.direction, "AxisLine direction")
        if not isinstance(self.origin, (tuple, list)) or len(self.origin) != 3:
            raise ValueError("AxisLine origin must be an XYZ point")
        origin = tuple(self.origin)
        for coordinate in origin:
            if isinstance(coordinate, bool) or not isfinite(_pv(coordinate)):
                raise ValueError(
                    "AxisLine origin must contain finite numeric CAD dimensions"
                )
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "origin", origin)

X, Y, Z = _AxisRef("X"), _AxisRef("Y"), _AxisRef("Z")

CENTER = Anchor.CENTER
TOP = Anchor.TOP
BOTTOM = Anchor.BOTTOM
LEFT = Anchor.LEFT
RIGHT = Anchor.RIGHT
FRONT = Anchor.FRONT
BACK = Anchor.BACK
UP = TOP
DOWN = BOTTOM
