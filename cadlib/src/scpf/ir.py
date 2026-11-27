"""Engine-neutral Forge semantic intermediate representation.

SCPF source is evaluated once into Forge model objects. This module normalizes
the backend-portable semantic subset into typed IR nodes before any native CAD
backend performs command lowering.

The transitional LegacyShapeIR is deliberately restricted to the stable
SolidCraft backend. It keeps the existing product surface working while that
surface is migrated node-by-node into explicit semantic IR.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Any

from .core import (
    Anchor,
    Edges,
    Expression,
    Faces,
    Parameter,
    Shape,
    _FaceBoundarySelection,
    _dim_add,
    _pv as pv,
    parameters_in,
)
from .scalar_ir import (
    ScalarBinaryIR,
    ScalarExpressionIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


@dataclass(frozen=True)
class ParameterIR:
    """One named editable Forge parameter with semantic use roles."""

    name: str
    value: float
    roles: tuple[str, ...] = ("length",)

    def __post_init__(self):
        if (
            not isinstance(self.roles, tuple)
            or not self.roles
            or any(role not in {"length", "angle"} for role in self.roles)
            or len(set(self.roles)) != len(self.roles)
            or self.roles != tuple(
                role for role in ("length", "angle") if role in self.roles
            )
        ):
            raise ValueError(
                "ParameterIR roles must be canonical length/angle roles"
            )

    @property
    def unit(self) -> str:
        """Compatibility view for native single-role parameter spelling."""
        if self.roles == ("length",):
            return "mm"
        if self.roles == ("angle",):
            return "deg"
        return ""


@dataclass(frozen=True)
class BoxIR:
    """Axis-aligned box geometry independent of placement."""

    length: Any
    width: Any
    height: Any
    source_kind: str = "box"


@dataclass(frozen=True)
class CylinderIR:
    """Principal-axis cylinder geometry independent of placement."""

    height: Any
    diameter: Any
    axis: str
    source_kind: str = "cylinder"


@dataclass(frozen=True)
class ConeIR:
    """Principal-axis cone/frustum geometry independent of placement."""

    height: Any
    diameter: Any
    top_diameter: Any
    axis: str
    source_kind: str = "cone"


@dataclass(frozen=True)
class SphereIR:
    """Spherical primitive geometry independent of native diameter spelling."""

    radius: Any
    source_kind: str = "sphere"


PrimitiveIR = BoxIR | CylinderIR | ConeIR | SphereIR


@dataclass(frozen=True)
class PlacementIR:
    """Absolute placement of one typed primitive.

    point is the world-space point at which the selected semantic anchor is
    placed. The native backend decides how that placement maps to its own
    primitive plane, centre/corner or base representation.
    """

    primitive: PrimitiveIR
    point: tuple[Any, Any, Any]
    anchor: tuple[int, int, int]
    explicit: bool = False
    source_kind: str = "placement"


@dataclass(frozen=True)
class CircleProfileIR:
    """One closed circular 2D profile inside a semantic Sketch."""

    diameter: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "circle"


@dataclass(frozen=True)
class PolygonProfileIR:
    """One closed straight-segment profile in Sketch-local coordinates."""

    points: tuple[tuple[Any, Any], ...]
    segment_ids: tuple[str, ...] | None = None
    source_kind: str = "polygon"

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or len(self.points) < 3
            or any(
                not isinstance(point, tuple) or len(point) != 2
                for point in self.points
            )
        ):
            raise ValueError(
                "PolygonProfileIR points must be at least three 2D tuples"
            )
        if self.segment_ids is not None:
            if (
                not isinstance(self.segment_ids, tuple)
                or len(self.segment_ids) != len(self.points)
                or any(
                    not isinstance(value, str) or not value
                    for value in self.segment_ids
                )
                or len(set(self.segment_ids)) != len(self.segment_ids)
            ):
                raise ValueError(
                    "PolygonProfileIR segment_ids must uniquely name every edge"
                )


ProfileIR = CircleProfileIR | PolygonProfileIR


@dataclass(frozen=True)
class PlaneIR:
    """Principal-orientation reference plane at a semantic XYZ origin."""

    orientation: str
    origin: tuple[Any, Any, Any] = (0, 0, 0)
    source_kind: str = "plane"

    def __post_init__(self):
        if self.orientation not in {"XY", "XZ", "YZ"}:
            raise ValueError("PlaneIR orientation must be XY, XZ or YZ")
        if (
            not isinstance(self.origin, tuple)
            or len(self.origin) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.origin
            )
        ):
            raise ValueError(
                "PlaneIR origin must contain three finite CAD dimensions"
            )


@dataclass(frozen=True)
class SketchPointIR:
    """One Sketch-local semantic point with authored symbolic coordinates."""

    position: tuple[Any, Any]

    def __post_init__(self):
        if (
            not isinstance(self.position, tuple)
            or len(self.position) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.position
            )
        ):
            raise ValueError(
                "SketchPointIR position must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class SketchLineIR:
    """Straight Sketch entity referencing semantic point tuple positions."""

    start: int
    end: int

    def __post_init__(self):
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end < 0
            or self.start == self.end
        ):
            raise ValueError(
                "SketchLineIR endpoints must be distinct non-negative point indexes"
            )


@dataclass(frozen=True)
class SketchOrientationConstraintIR:
    """Horizontal/vertical semantic relation on one Sketch-local line."""

    line: int
    orientation: str

    def __post_init__(self):
        if type(self.line) is not int or self.line < 0:
            raise ValueError(
                "SketchOrientationConstraintIR line must be a non-negative index"
            )
        if self.orientation not in {"horizontal", "vertical"}:
            raise ValueError(
                "SketchOrientationConstraintIR orientation must be horizontal or vertical"
            )


@dataclass(frozen=True)
class SketchLengthDimensionIR:
    """One symbolic driving length attached to a Sketch-local line."""

    line: int
    value: Any

    def __post_init__(self):
        if type(self.line) is not int or self.line < 0:
            raise ValueError(
                "SketchLengthDimensionIR line must be a non-negative index"
            )
        if isinstance(self.value, bool) or not isfinite(pv(self.value)):
            raise ValueError(
                "SketchLengthDimensionIR value must be one finite CAD dimension"
            )
        if pv(self.value) <= 0:
            raise ValueError(
                "SketchLengthDimensionIR value must be positive"
            )


@dataclass(frozen=True)
class SketchCoordinateDimensionIR:
    """Signed Sketch-local point coordinate relative to the Sketch origin."""

    point: int
    axis: str
    value: Any

    def __post_init__(self):
        if type(self.point) is not int or self.point < 0:
            raise ValueError(
                "SketchCoordinateDimensionIR point must be a non-negative index"
            )
        if self.axis not in {"x", "y"}:
            raise ValueError(
                "SketchCoordinateDimensionIR axis must be x or y"
            )
        if isinstance(self.value, bool) or not isfinite(pv(self.value)):
            raise ValueError(
                "SketchCoordinateDimensionIR value must be one finite CAD dimension"
            )


@dataclass(frozen=True)
class SketchRelationsIR:
    """Explicit Sketch entity/constraint/dimension graph.

    Integer references are positions inside these semantic tuples. They are
    never native ids, replay names or backend command indexes.
    """

    points: tuple[SketchPointIR, ...]
    lines: tuple[SketchLineIR, ...]
    constraints: tuple[SketchOrientationConstraintIR, ...] = ()
    dimensions: tuple[SketchLengthDimensionIR, ...] = ()
    coordinate_dimensions: tuple[SketchCoordinateDimensionIR, ...] = ()

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or any(not isinstance(point, SketchPointIR) for point in self.points)
        ):
            raise ValueError("SketchRelationsIR requires semantic points")
        if (
            not isinstance(self.lines, tuple)
            or not self.lines
            or any(not isinstance(line, SketchLineIR) for line in self.lines)
        ):
            raise ValueError("SketchRelationsIR requires semantic lines")
        point_count = len(self.points)
        if any(
            line.start >= point_count or line.end >= point_count
            for line in self.lines
        ):
            raise ValueError(
                "SketchRelationsIR line references a missing semantic point"
            )
        line_count = len(self.lines)
        if any(
            constraint.line >= line_count
            for constraint in self.constraints
        ):
            raise ValueError(
                "SketchRelationsIR constraint references a missing semantic line"
            )
        if any(
            dimension.line >= line_count
            for dimension in self.dimensions
        ):
            raise ValueError(
                "SketchRelationsIR dimension references a missing semantic line"
            )
        if any(
            dimension.point >= point_count
            for dimension in self.coordinate_dimensions
        ):
            raise ValueError(
                "SketchRelationsIR coordinate dimension references a missing semantic point"
            )


@dataclass(frozen=True)
class SketchIR:
    """Standalone 2D sketch geometry independent of downstream features."""

    name: str
    plane: PlaneIR
    profiles: tuple[ProfileIR, ...]
    relations: SketchRelationsIR | None = None
    source_kind: str = "sketch"

    def __post_init__(self):
        if not isinstance(self.plane, PlaneIR):
            raise ValueError("SketchIR plane must be PlaneIR")
        if self.relations is not None and not isinstance(
            self.relations, SketchRelationsIR
        ):
            raise ValueError("SketchIR relations must be SketchRelationsIR")


@dataclass(frozen=True)
class RegionIR:
    """Closed sketch region described by semantic profile membership."""

    outer: int
    holes: tuple[int, ...] = ()

    def __post_init__(self):
        if type(self.outer) is not int or self.outer < 0:
            raise ValueError("RegionIR outer must be a non-negative profile index")
        if (
            not isinstance(self.holes, tuple)
            or any(type(index) is not int or index < 0 for index in self.holes)
        ):
            raise ValueError(
                "RegionIR holes must contain non-negative profile indexes"
            )
        if self.outer in self.holes:
            raise ValueError("RegionIR outer profile cannot also be a hole")
        if len(set(self.holes)) != len(self.holes):
            raise ValueError("RegionIR hole profile indexes must be unique")


def _circle_profile_radii(sketch: SketchIR) -> tuple[float, ...]:
    """Validate the bounded concentric Circle profile family and return radii."""
    if not sketch.profiles:
        raise ValueError("qualified circle region requires CircleProfileIR profiles")

    radii = []
    for profile in sketch.profiles:
        if not isinstance(profile, CircleProfileIR):
            raise ValueError(
                "qualified circle region requires CircleProfileIR profiles"
            )
        if tuple(profile.center) != (0, 0):
            raise ValueError(
                "qualified circle region currently requires origin centers"
            )
        diameter = pv(profile.diameter)
        if not isfinite(diameter) or diameter <= 0:
            raise ValueError(
                "qualified circle region diameters must be positive"
            )
        radii.append(diameter / 2.0)

    epsilon = 1e-12
    ordered = sorted(radii)
    if any(
        abs(right - left) <= epsilon
        for left, right in zip(ordered, ordered[1:])
    ):
        raise ValueError(
            "qualified concentric circle region requires distinct diameters"
        )
    return tuple(radii)


def _concentric_circle_region_from_pick(
    sketch: SketchIR,
    pick,
) -> RegionIR:
    """Resolve one authored exact-region pick to adjacent semantic boundaries."""
    if (
        not isinstance(pick, (tuple, list))
        or len(pick) != 2
    ):
        raise ValueError("circle exact-region pick must be one 2D point")
    try:
        coordinates = tuple(float(pv(value)) for value in pick)
    except (TypeError, ValueError):
        raise ValueError("circle exact-region pick must be finite") from None
    if any(not isfinite(value) for value in coordinates):
        raise ValueError("circle exact-region pick must be finite")

    radii = _circle_profile_radii(sketch)
    pick_radius = hypot(*coordinates)
    epsilon = 1e-12
    if any(abs(radius - pick_radius) <= epsilon for radius in radii):
        raise ValueError("circle exact-region pick lies on a profile boundary")

    enclosing = [
        (radius, index)
        for index, radius in enumerate(radii)
        if radius > pick_radius
    ]
    if not enclosing:
        raise ValueError("circle exact-region pick lies outside every profile")
    outer_radius, outer_index = min(enclosing)

    inner = [
        (radius, index)
        for index, radius in enumerate(radii)
        if radius < pick_radius
    ]
    if not inner:
        return RegionIR(outer=outer_index)

    _inner_radius, inner_index = max(inner)
    return RegionIR(outer=outer_index, holes=(inner_index,))


def _circle_region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Return one deterministic selector inside a typed concentric circle region.

    RegionIR owns only the immediate boundary profiles of the selected connected
    region. Other concentric profiles may remain in the Sketch without becoming
    region members.
    """
    indexes = (region.outer,) + region.holes
    if any(index >= len(sketch.profiles) for index in indexes):
        raise ValueError("circle region references a missing sketch profile")
    if len(region.holes) > 1:
        raise ValueError(
            "qualified concentric circle region supports at most one hole"
        )

    radii = _circle_profile_radii(sketch)
    outer_radius = radii[region.outer]
    epsilon = 1e-12

    if not region.holes:
        if any(
            index != region.outer and radius < outer_radius - epsilon
            for index, radius in enumerate(radii)
        ):
            raise ValueError(
                "qualified no-hole circle region must use the innermost profile"
            )
        return (0.0, 0.0)

    inner_index = region.holes[0]
    inner_radius = radii[inner_index]
    if outer_radius <= inner_radius + epsilon:
        raise ValueError(
            "qualified annular circle region requires outer diameter above inner"
        )
    if any(
        index not in (region.outer, inner_index)
        and inner_radius + epsilon < radius < outer_radius - epsilon
        for index, radius in enumerate(radii)
    ):
        raise ValueError(
            "qualified annular circle region boundaries must be adjacent profiles"
        )

    # Midway between the two radii is strictly inside the selected annulus.
    return ((outer_radius + inner_radius) / 2.0, 0.0)


def _polygon_region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Return deterministic transport geometry for one simple semantic polygon.

    Symbolic coordinates remain untouched in PolygonProfileIR. Current values
    are evaluated only to validate a finite, non-self-intersecting region and
    derive an interior selector when a native API requires one.
    """

    if (
        len(sketch.profiles) != 1
        or region.outer != 0
        or region.holes
        or not isinstance(sketch.profiles[0], PolygonProfileIR)
    ):
        raise ValueError(
            "qualified polygon region requires one outer PolygonProfileIR"
        )

    profile = sketch.profiles[0]
    points = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in points for value in point):
        raise ValueError("qualified polygon region coordinates must be finite")
    if len(set(points)) != len(points):
        raise ValueError("qualified polygon region has duplicate vertices")

    epsilon = 1e-12
    count = len(points)
    for index in range(count):
        a = points[index]
        b = points[(index + 1) % count]
        if hypot(b[0] - a[0], b[1] - a[1]) <= epsilon:
            raise ValueError("qualified polygon region has a zero-length edge")

    def orientation(a, b, c):
        return (
            (b[0] - a[0]) * (c[1] - a[1])
            - (b[1] - a[1]) * (c[0] - a[0])
        )

    def on_segment(a, b, p):
        return (
            min(a[0], b[0]) - epsilon <= p[0] <= max(a[0], b[0]) + epsilon
            and min(a[1], b[1]) - epsilon <= p[1] <= max(a[1], b[1]) + epsilon
            and abs(orientation(a, b, p)) <= epsilon
        )

    def segments_intersect(a, b, c, d):
        o1 = orientation(a, b, c)
        o2 = orientation(a, b, d)
        o3 = orientation(c, d, a)
        o4 = orientation(c, d, b)
        if (
            ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon))
            and ((o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon))
        ):
            return True
        return (
            (abs(o1) <= epsilon and on_segment(a, b, c))
            or (abs(o2) <= epsilon and on_segment(a, b, d))
            or (abs(o3) <= epsilon and on_segment(c, d, a))
            or (abs(o4) <= epsilon and on_segment(c, d, b))
        )

    # Reject bow-ties, touching non-neighbour edges and other ambiguous loops.
    for left in range(count):
        a = points[left]
        b = points[(left + 1) % count]
        for right in range(left + 1, count):
            if right == left:
                continue
            if right == (left + 1) % count:
                continue
            if left == (right + 1) % count:
                continue
            c = points[right]
            d = points[(right + 1) % count]
            if segments_intersect(a, b, c, d):
                raise ValueError(
                    "qualified polygon region must be a simple non-self-intersecting polygon"
                )

    twice_area = sum(
        points[index][0] * points[(index + 1) % count][1]
        - points[(index + 1) % count][0] * points[index][1]
        for index in range(count)
    )
    if abs(twice_area) <= epsilon:
        raise ValueError("qualified polygon region must enclose non-zero area")

    # Pick a horizontal scanline strictly between authored vertex levels.
    # A simple polygon intersects such a line in interior pairs. The midpoint
    # of the widest interval is strictly inside and is independent of winding.
    levels = sorted({point[1] for point in points})
    candidates = []
    for low, high in zip(levels, levels[1:]):
        if high - low <= epsilon:
            continue
        y = (low + high) / 2.0
        intersections = []
        for index in range(count):
            a = points[index]
            b = points[(index + 1) % count]
            if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                x = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                intersections.append(x)
        intersections.sort()
        if len(intersections) % 2:
            raise ValueError(
                "qualified polygon region has ambiguous scanline intersections"
            )
        for first, second in zip(intersections[0::2], intersections[1::2]):
            width = second - first
            if width > epsilon:
                candidates.append((width, (first + second) / 2.0, y))

    if not candidates:
        raise ValueError(
            "qualified polygon region has no deterministic interior selector"
        )

    _width, x, y = max(
        candidates,
        key=lambda item: (item[0], -abs(item[2]), -abs(item[1])),
    )
    return (x, y)


def _region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Derive backend transport from semantic profile/region geometry."""

    if (
        0 <= region.outer < len(sketch.profiles)
        and isinstance(sketch.profiles[region.outer], PolygonProfileIR)
    ):
        return _polygon_region_interior_point(sketch, region)
    return _circle_region_interior_point(sketch, region)


@dataclass(frozen=True)
class ExtrudeIR:
    """Distance extrusion over semantic Sketch regions."""

    sketch: SketchIR
    regions: tuple[RegionIR, ...]
    distance: Any
    direction: str
    source_kind: str = "sketch_base_extrusion"


@dataclass(frozen=True)
class AxisLineIR:
    """Engine-neutral principal-direction axis through a semantic XYZ point."""

    direction: str
    origin: tuple[Any, Any, Any] = (0, 0, 0)
    source_kind: str = "axis_line"

    def __post_init__(self):
        if self.direction not in {"X", "Y", "Z"}:
            raise ValueError("AxisLineIR direction must be X, Y or Z")
        if (
            not isinstance(self.origin, tuple)
            or len(self.origin) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.origin
            )
        ):
            raise ValueError(
                "AxisLineIR origin must contain three finite CAD dimensions"
            )


@dataclass(frozen=True)
class RevolveIR:
    """Angular sweep of one Sketch region as one authored body feature."""

    sketch: SketchIR
    region: RegionIR
    axis: AxisLineIR
    angle: Any
    direction: str | None = None
    operation: str = "new_body"
    target: PlacementIR | None = None
    source_kind: str = "sketch_base_revolve"

    def __post_init__(self):
        if not isinstance(self.axis, AxisLineIR):
            raise ValueError("RevolveIR axis must be AxisLineIR")
        if self.direction not in (None, "symmetric"):
            raise ValueError("RevolveIR direction must be None or symmetric")
        if self.operation not in {"new_body", "cut"}:
            raise ValueError("RevolveIR operation must be new_body or cut")
        if self.operation == "new_body" and self.target is not None:
            raise ValueError("new-body RevolveIR must not have a target")
        if self.operation == "cut" and not isinstance(self.target, PlacementIR):
            raise ValueError("cut RevolveIR requires one typed target placement")


@dataclass(frozen=True)
class FaceBoundaryIR:
    """Semantic request for all boundary edges of cardinal planar faces."""

    faces: tuple[str, ...]


@dataclass(frozen=True)
class ParallelEdgeSetIR:
    """Semantic request for straight edges parallel to one principal axis."""

    axis: str

    def __post_init__(self):
        if self.axis not in {"X", "Y", "Z"}:
            raise ValueError("ParallelEdgeSetIR axis must be X, Y or Z")


@dataclass(frozen=True)
class FilletIR:
    """Constant-radius fillet over one qualified typed body result."""

    base: PlacementIR
    radius: Any
    edges: ParallelEdgeSetIR
    source_kind: str = "fillet"

    def __post_init__(self):
        if not isinstance(self.base, PlacementIR):
            raise ValueError("FilletIR base must be PlacementIR")
        if not isinstance(self.base.primitive, BoxIR):
            raise ValueError("FilletIR first qualified base must be BoxIR")
        if not isinstance(self.edges, ParallelEdgeSetIR):
            raise ValueError("FilletIR edges must be ParallelEdgeSetIR")
        if (
            isinstance(self.radius, bool)
            or not isfinite(pv(self.radius))
            or pv(self.radius) <= 0
        ):
            raise ValueError("FilletIR radius must be one positive CAD dimension")


@dataclass(frozen=True)
class ChamferIR:
    """One semantic chamfer over a qualified typed body result."""

    base: "PlacementIR | ExtrudeIR"
    distance: Any
    edges: FaceBoundaryIR
    distance2: Any | None = None
    flip: bool = False
    source_kind: str = "chamfer"

    def __post_init__(self):
        if not isinstance(self.flip, bool):
            raise ValueError("ChamferIR flip must be bool")
        if self.flip and self.distance2 is None:
            raise ValueError("ChamferIR flip requires distance2")


@dataclass(frozen=True)
class BooleanIR:
    """Bounded recursive primitive CSG intent.

    target may be another BooleanIR so a left-associated public CSG expression
    remains one semantic tree. tool is deliberately one placed primitive in
    the current qualified slice; more general boolean operands stay legacy.
    """

    operation: str
    target: "PlacementIR | FilletIR | BooleanIR"
    tool: PlacementIR
    source_kind: str = "boolean"

    def __post_init__(self):
        if self.operation not in {"join", "cut", "intersect"}:
            raise ValueError(
                "BooleanIR operation must be join, cut or intersect"
            )


@dataclass(frozen=True)
class LegacyShapeIR:
    """Transitional wrapper for stable SolidCraft surface not migrated yet."""

    shape: Shape
    source_kind: str


IRNode = (
    PlacementIR
    | ExtrudeIR
    | RevolveIR
    | ChamferIR
    | FilletIR
    | BooleanIR
    | LegacyShapeIR
)


@dataclass(frozen=True)
class FeatureRefIR:
    """Engine-neutral semantic reference to one normalized authored feature."""

    path: tuple[str, ...]

    def __post_init__(self):
        if (
            not isinstance(self.path, tuple)
            or not self.path
            or any(
                not isinstance(segment, str)
                or not segment
                or not segment.replace("_", "").isalnum()
                for segment in self.path
            )
        ):
            raise ValueError(
                "FeatureRefIR path must contain semantic non-empty path segments"
            )


@dataclass(frozen=True)
class SuppressionColumnIR:
    """One configuration column that suppresses an exact semantic feature."""

    feature: FeatureRefIR

    def __post_init__(self):
        if not isinstance(self.feature, FeatureRefIR):
            raise ValueError("SuppressionColumnIR feature must be FeatureRefIR")


@dataclass(frozen=True)
class ConfigurationRowIR:
    """One named row of typed configuration cells."""

    name: str
    cells: tuple[bool, ...]

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("ConfigurationRowIR name must be non-empty text")
        if (
            not isinstance(self.cells, tuple)
            or any(not isinstance(cell, bool) for cell in self.cells)
        ):
            raise ValueError(
                "suppression-only ConfigurationRowIR cells must be bool"
            )


@dataclass(frozen=True)
class ConfigurationIR:
    """Bounded engine-neutral configuration table for semantic suppression."""

    active: str
    columns: tuple[SuppressionColumnIR, ...]
    rows: tuple[ConfigurationRowIR, ...]

    def __post_init__(self):
        if (
            not isinstance(self.columns, tuple)
            or not self.columns
            or any(
                not isinstance(column, SuppressionColumnIR)
                for column in self.columns
            )
        ):
            raise ValueError(
                "suppression-only ConfigurationIR requires suppression columns"
            )
        if (
            not isinstance(self.rows, tuple)
            or not self.rows
            or any(not isinstance(row, ConfigurationRowIR) for row in self.rows)
        ):
            raise ValueError("ConfigurationIR requires named rows")
        if len({row.name for row in self.rows}) != len(self.rows):
            raise ValueError("ConfigurationIR row names must be unique")
        if self.active not in {row.name for row in self.rows}:
            raise ValueError(
                "ConfigurationIR active row must name a declared row"
            )
        if any(len(row.cells) != len(self.columns) for row in self.rows):
            raise ValueError(
                "ConfigurationIR row cell count must match column count"
            )


@dataclass(frozen=True)
class ModelIR:
    """One normalized Forge model independent of a native CAD backend."""

    root: IRNode
    parameters: tuple[ParameterIR, ...]
    configuration: ConfigurationIR | None = None

    def __post_init__(self):
        if (
            self.configuration is not None
            and not isinstance(self.configuration, ConfigurationIR)
        ):
            raise ValueError(
                "ModelIR configuration must be ConfigurationIR or None"
            )


def _collect_parameters(value, found=None):
    """Collect named symbolic parameters in deterministic first-use order."""
    if found is None:
        found = {}

    if isinstance(value, Shape):
        _collect_parameters(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _collect_parameters(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _collect_parameters(item, found)
        return found

    for parameter in parameters_in(value):
        previous = found.setdefault(parameter.name, parameter.value)
        if previous != parameter.value:
            raise ValueError(
                f"conflicting values for parameter {parameter.name}"
            )
    return found


def _angle_parameter_names(value, found=None):
    """Collect parameters whose qualified semantic role is an angle."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "sketch_base_revolve":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                angle,
                _axis,
                _direction,
                _operations,
                _rotation,
            ) = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
        _angle_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _angle_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _angle_parameter_names(item, found)
    return found


def _length_parameter_names(value, found=None):
    """Collect parameters used in the currently-qualified length-valued slots."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "sketch_base_revolve":
            # The Revolve sweep is the only currently-qualified angle-valued
            # Shape payload. Every other symbolic value in this payload retains
            # the pre-existing CAD-length interpretation.
            for index, item in enumerate(value.data):
                if index != 5:
                    _length_parameter_names(item, found)
            return found
        _length_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _length_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _length_parameter_names(item, found)
        return found

    found.update(parameter.name for parameter in parameters_in(value))
    return found


def _parameter_ir(shape: Shape) -> tuple[ParameterIR, ...]:
    values = _collect_parameters(shape)
    length_parameters = _length_parameter_names(shape)
    angle_parameters = _angle_parameter_names(shape)
    return tuple(
        ParameterIR(
            name,
            value,
            roles=tuple(
                role
                for role, names in (
                    ("length", length_parameters),
                    ("angle", angle_parameters),
                )
                if name in names
            ),
        )
        for name, value in values.items()
    )


def _anchor_vector(anchor) -> tuple[int, int, int]:
    return tuple(int(value) for value in anchor.vector)


def _shift_point(point, delta):
    return tuple(
        _dim_add(current, added)
        for current, added in zip(point, delta)
    )


def _portable_placement(shape: Shape) -> PlacementIR | None:
    """Normalize supported primitive/placement authoring into one IR form."""
    if shape.kind == "box":
        length, width, height, anchor = shape.data
        return PlacementIR(
            primitive=BoxIR(length=length, width=width, height=height),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "cylinder":
        height, diameter, axis, anchor = shape.data
        return PlacementIR(
            primitive=CylinderIR(
                height=height,
                diameter=diameter,
                axis=axis,
            ),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "cone":
        height, diameter, top_diameter, axis, anchor = shape.data
        return PlacementIR(
            primitive=ConeIR(
                height=height,
                diameter=diameter,
                top_diameter=top_diameter,
                axis=axis,
            ),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "sphere":
        radius, anchor = shape.data
        return PlacementIR(
            primitive=SphereIR(radius=radius),
            point=(0, 0, 0),
            anchor=_anchor_vector(anchor),
        )

    if shape.kind == "placed_box":
        box, x, y, z, anchor = shape.data
        if box.kind != "box":
            return None
        length, width, height, _constructor_anchor = box.data
        return PlacementIR(
            primitive=BoxIR(length=length, width=width, height=height),
            point=(x, y, z),
            anchor=_anchor_vector(anchor),
            explicit=True,
        )

    if shape.kind == "placed3d":
        child, x, y, z = shape.data
        if child.kind == "cylinder":
            height, diameter, axis, anchor = child.data
            primitive = CylinderIR(
                height=height,
                diameter=diameter,
                axis=axis,
            )
        elif child.kind == "cone":
            height, diameter, top_diameter, axis, anchor = child.data
            primitive = ConeIR(
                height=height,
                diameter=diameter,
                top_diameter=top_diameter,
                axis=axis,
            )
        else:
            return None
        return PlacementIR(
            primitive=primitive,
            point=(x, y, z),
            anchor=_anchor_vector(anchor),
            explicit=True,
        )

    if shape.kind == "translated":
        child, delta = shape.data
        placement = _portable_placement(child)
        if placement is None:
            return None
        return PlacementIR(
            primitive=placement.primitive,
            point=_shift_point(placement.point, delta),
            anchor=placement.anchor,
            explicit=True,
        )

    return None


def _portable_csg_placement(node: IRNode) -> bool:
    """Accept the already-qualified primitive PlacementIR forms inside CSG."""
    return (
        isinstance(node, PlacementIR)
        and isinstance(node.primitive, (BoxIR, CylinderIR, ConeIR, SphereIR))
    )


_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}
_PLANE_AXES = {
    "XY": {"X", "Y"},
    "XZ": {"X", "Z"},
    "YZ": {"Y", "Z"},
}


def _plane_ir(orientation: str, offset=None) -> PlaneIR | None:
    """Normalize one principal standalone Sketch plane without native ids."""
    if orientation not in _PLANE_NORMAL_INDEX:
        return None
    distance = 0 if offset is None else offset
    origin = [0, 0, 0]
    origin[_PLANE_NORMAL_INDEX[orientation]] = distance
    try:
        return PlaneIR(orientation=orientation, origin=tuple(origin))
    except ValueError:
        return None


def _semantic_dimension_key(value):
    """Identity key for authored CAD dimensions without evaluating symbols."""
    parameters = parameters_in(value)
    if not parameters:
        return ("number", float(pv(value)))
    expression = getattr(value, "expression", None)
    if not isinstance(expression, str) or not expression:
        return None
    return (
        "expression",
        expression,
        tuple(parameter.name for parameter in parameters),
    )


def _same_semantic_dimension(left, right) -> bool:
    """Compare authored dimension intent, using values only when non-symbolic."""
    if left is right:
        return True
    left_key = _semantic_dimension_key(left)
    right_key = _semantic_dimension_key(right)
    if left_key is None or right_key is None:
        return False
    if left_key[0] == right_key[0] == "number":
        return abs(left_key[1] - right_key[1]) <= 1e-12
    return left_key == right_key


def _parameterized_rectangle_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize the bounded #440 rectangle relation graph before lowering."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or len(profile.points) != 4
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    p1, p2, p3, p4 = profile.points
    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    # This first slice is deliberately the already-qualified origin-based
    # axis-aligned rectangle from native-revolve. Compare symbolic equality
    # without baking current values into semantic identity.
    if any(parameters_in(value) for value in (p1[0], p1[1], p2[0], p4[1])):
        return None
    if (
        abs(values[0][0]) > 1e-12
        or abs(values[0][1]) > 1e-12
        or abs(values[1][0]) > 1e-12
        or abs(values[3][1]) > 1e-12
        or not _same_semantic_dimension(p2[1], p3[1])
        or not _same_semantic_dimension(p3[0], p4[0])
        or values[1][1] <= 0
        or values[2][0] <= 0
    ):
        return None

    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=(
            SketchLineIR(0, 1),
            SketchLineIR(1, 2),
            SketchLineIR(2, 3),
            SketchLineIR(3, 0),
        ),
        constraints=(
            SketchOrientationConstraintIR(0, "vertical"),
            SketchOrientationConstraintIR(1, "horizontal"),
            SketchOrientationConstraintIR(2, "vertical"),
            SketchOrientationConstraintIR(3, "horizontal"),
        ),
        dimensions=(
            SketchLengthDimensionIR(0, p2[1]),
            SketchLengthDimensionIR(1, p3[0]),
        ),
    )


def _parameterized_polygon_coordinate_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize generic parameterized Polygon point coordinates into Sketch IR."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    point_count = len(profile.points)
    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=tuple(
            SketchLineIR(index, (index + 1) % point_count)
            for index in range(point_count)
        ),
        coordinate_dimensions=tuple(
            SketchCoordinateDimensionIR(
                point=index,
                axis=axis,
                value=point[coordinate],
            )
            for index, point in enumerate(profile.points)
            for coordinate, axis in enumerate(("x", "y"))
        ),
    )


def _portable_extrude(shape: Shape) -> ExtrudeIR | None:
    """Normalize the qualified standalone Sketch + Extrude slices."""
    if shape.kind != "sketch_base_extrusion":
        return None

    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        distance,
        direction,
        operations,
        profile_picks,
        exact_regions,
        rotation,
    ) = shape.data

    if plane not in ("XY", "XZ", "YZ"):
        return None
    if origin is not None or plane_offset is not None or rotation is not None:
        return None
    plane_ir = _plane_ir(plane)
    if plane_ir is None:
        return None
    if operations:
        return None
    if direction not in ("positive", "negative", "symmetric"):
        return None

    # Bounded straight-segment feature-composition slice (#351).
    if len(profiles) == 1 and profiles[0][0].kind == "polygon":
        if direction != "symmetric":
            return None
        if profile_picks is not None or exact_regions:
            return None

        profile, profile_anchor, offset = profiles[0]
        if profile_anchor is not None or tuple(offset) != (0, 0):
            return None
        points, profile_plane, ids = profile.data
        if profile_plane != plane:
            return None

        polygon = PolygonProfileIR(
            points=tuple(tuple(point) for point in points),
            segment_ids=tuple(ids) if ids is not None else None,
        )
        sketch = SketchIR(
            name=sketch_name,
            plane=plane_ir,
            profiles=(polygon,),
            relations=(
                _parameterized_rectangle_relations(polygon)
                or _parameterized_polygon_coordinate_relations(polygon)
            ),
        )
        region = RegionIR(outer=0)
        try:
            _polygon_region_interior_point(sketch, region)
        except ValueError:
            return None
        return ExtrudeIR(
            sketch=sketch,
            regions=(region,),
            distance=distance,
            direction=direction,
        )

    # Circle exact-region slices qualified by #282/#320/#456.
    if direction not in ("positive", "negative"):
        return None
    if not profiles:
        return None

    semantic_profiles = []
    for profile, profile_anchor, offset in profiles:
        if profile.kind != "circle":
            return None
        if profile_anchor is not Anchor.CENTER:
            return None
        if tuple(offset) != (0, 0):
            return None
        (diameter,) = profile.data
        semantic_profiles.append(CircleProfileIR(diameter=diameter))

    sketch = SketchIR(
        name=sketch_name,
        plane=plane_ir,
        profiles=tuple(semantic_profiles),
    )

    if len(semantic_profiles) == 1:
        if profile_picks is not None or exact_regions:
            return None
        region = RegionIR(outer=0)
        try:
            _circle_region_interior_point(sketch, region)
        except ValueError:
            return None
        regions = (region,)
    else:
        if not exact_regions or profile_picks is None or len(profile_picks) != 1:
            return None
        try:
            region = _concentric_circle_region_from_pick(
                sketch,
                profile_picks[0],
            )
            _circle_region_interior_point(sketch, region)
        except ValueError:
            return None
        regions = (region,)

    return ExtrudeIR(
        sketch=sketch,
        regions=regions,
        distance=distance,
        direction=direction,
    )


def _axis_line_ir(axis) -> AxisLineIR | None:
    """Normalize public principal/custom axis intent without native ids."""
    if isinstance(axis, str):
        if axis not in {"X", "Y", "Z"}:
            return None
        return AxisLineIR(direction=axis)

    if (
        not isinstance(axis, (tuple, list))
        or len(axis) != 2
    ):
        return None
    origin, direction = axis
    if (
        not isinstance(origin, (tuple, list))
        or len(origin) != 3
        or not isinstance(direction, (tuple, list))
        or len(direction) != 3
    ):
        return None

    vector = tuple(float(value) for value in direction)
    principal = {
        "X": (1.0, 0.0, 0.0),
        "Y": (0.0, 1.0, 0.0),
        "Z": (0.0, 0.0, 1.0),
    }
    semantic_direction = next(
        (
            name
            for name, expected in principal.items()
            if all(
                abs(actual - wanted) <= 1e-12
                for actual, wanted in zip(vector, expected)
            )
        ),
        None,
    )
    if semantic_direction is None:
        return None

    try:
        return AxisLineIR(
            direction=semantic_direction,
            origin=tuple(origin),
        )
    except ValueError:
        return None


def _axis_line_in_sketch_plane(axis: AxisLineIR, plane: PlaneIR) -> bool:
    """Check semantic coplanarity for the bounded principal-plane slice."""
    if (
        not isinstance(plane, PlaneIR)
        or axis.direction not in _PLANE_AXES[plane.orientation]
    ):
        return False
    normal_index = _PLANE_NORMAL_INDEX[plane.orientation]
    return _same_semantic_dimension(
        axis.origin[normal_index],
        plane.origin[normal_index],
    )


def _portable_revolve(
    shape: Shape,
    *,
    operation: str = "new_body",
    target: PlacementIR | None = None,
) -> RevolveIR | None:
    """Normalize the qualified standalone/cut Sketch + Revolve semantic slice."""
    if shape.kind != "sketch_base_revolve":
        return None

    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        angle,
        axis,
        direction,
        operations,
        rotation,
    ) = shape.data

    if plane not in ("XY", "XZ", "YZ"):
        return None
    if origin is not None or rotation is not None:
        return None
    plane_ir = _plane_ir(plane, plane_offset)
    if plane_ir is None:
        return None
    if operations or direction is not None:
        return None
    if operation not in {"new_body", "cut"}:
        return None
    if operation == "new_body" and target is not None:
        return None
    if operation == "cut" and not isinstance(target, PlacementIR):
        return None
    if len(profiles) != 1:
        return None

    axis_ir = _axis_line_ir(axis)
    if axis_ir is None or not _axis_line_in_sketch_plane(axis_ir, plane_ir):
        return None

    profile, profile_anchor, offset = profiles[0]
    if (
        profile.kind != "polygon"
        or profile_anchor is not None
        or tuple(offset) != (0, 0)
    ):
        return None

    points, profile_plane, ids = profile.data
    if profile_plane != plane:
        return None

    sweep = pv(angle)
    if not isfinite(sweep) or sweep <= 0 or sweep > 360:
        return None

    angle_parameters = {
        parameter.name for parameter in parameters_in(angle)
    }
    coordinate_parameters = {
        parameter.name
        for point in points
        for value in point
        for parameter in parameters_in(value)
    }
    mixed_parameters = angle_parameters & coordinate_parameters
    if mixed_parameters:
        # #481 extends #469 from one direct Parameter to authored affine
        # scalar expressions whose operation tree is captured semantically.
        # Text-only expressions remain outside the portable slice; no backend
        # or normalizer is allowed to recover meaning by parsing their text.
        if len(mixed_parameters) != 1:
            return None
        mixed_name = next(iter(mixed_parameters))
        if not isinstance(angle, Parameter) or angle.name != mixed_name:
            return None
        mixed_coordinate_uses = [
            value
            for point in points
            for value in point
            if any(
                parameter.name == mixed_name
                for parameter in parameters_in(value)
            )
        ]
        for value in mixed_coordinate_uses:
            if isinstance(value, Parameter) and value.name == mixed_name:
                continue
            if (
                isinstance(value, Expression)
                and value.scalar_ir is not None
                and mixed_name in scalar_parameter_names(value.scalar_ir)
                and is_affine_scalar_expression(value.scalar_ir)
            ):
                continue
            return None

    polygon = PolygonProfileIR(
        points=tuple(tuple(point) for point in points),
        segment_ids=tuple(ids) if ids is not None else None,
    )
    sketch = SketchIR(
        name=sketch_name,
        plane=plane_ir,
        profiles=(polygon,),
        relations=(
            _parameterized_rectangle_relations(polygon)
            or _parameterized_polygon_coordinate_relations(polygon)
        ),
    )
    region = RegionIR(outer=0)
    try:
        _polygon_region_interior_point(sketch, region)
    except ValueError:
        return None

    return RevolveIR(
        sketch=sketch,
        region=region,
        axis=axis_ir,
        angle=angle,
        direction=direction,
        operation=operation,
        target=target,
    )



def _portable_fillet(shape: Shape) -> FilletIR | None:
    """Normalize the first semantic constant-radius principal-edge Fillet."""
    if shape.kind != "fillet" or len(shape.data) != 3:
        return None

    base, radius, edges = shape.data
    if edges is not Edges.VERTICAL:
        return None
    if (
        isinstance(radius, bool)
        or not isinstance(radius, (int, float, Parameter))
        or not isfinite(pv(radius))
        or pv(radius) <= 0
    ):
        return None

    placement = _portable_placement(base)
    if placement is None or not isinstance(placement.primitive, BoxIR):
        return None

    return FilletIR(
        base=placement,
        radius=radius,
        edges=ParallelEdgeSetIR("Z"),
    )


def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    if shape.kind != "chamfer":
        return None

    if len(shape.data) == 3:
        # Compatibility with the pre-#271 equal-distance frontend payload.
        base, distance, edges = shape.data
        distance2 = None
        flip = False
    elif len(shape.data) == 5:
        base, distance, edges, distance2, flip = shape.data
    else:
        return None

    if not isinstance(flip, bool):
        return None
    if flip and distance2 is None:
        return None
    if not isinstance(edges, _FaceBoundarySelection) or not edges.faces:
        return None

    semantic_faces = tuple(Faces(face).value for face in edges.faces)
    asymmetric = distance2 is not None

    placement = _portable_placement(base)
    if placement is not None:
        if (
            not isinstance(placement.primitive, BoxIR)
            or len(semantic_faces) != 1
        ):
            return None
        if asymmetric and semantic_faces != ("top",):
            # #485 proves the unambiguous SolidCraft "up-most first face"
            # orientation only for one semantic TOP boundary.
            return None
        base_ir: PlacementIR | ExtrudeIR = placement
    else:
        extrude = _portable_extrude(base)
        if (
            extrude is None
            or asymmetric
            or flip
            or extrude.direction != "symmetric"
            or extrude.sketch.plane.orientation != "XZ"
            or extrude.sketch.plane.origin != (0, 0, 0)
            or len(extrude.sketch.profiles) != 1
            or not isinstance(extrude.sketch.profiles[0], PolygonProfileIR)
            or semantic_faces != ("front", "back")
        ):
            return None
        base_ir = extrude

    return ChamferIR(
        base=base_ir,
        distance=distance,
        edges=FaceBoundaryIR(semantic_faces),
        distance2=distance2,
        flip=flip,
    )


def _normalize_node(shape: Shape) -> IRNode:
    placement = _portable_placement(shape)
    if placement is not None:
        return placement

    if shape.kind in {"union", "difference", "intersection"}:
        target_shape, tool_shape = shape.data

        # Preserve an authored subtractive Revolve as that feature rather than
        # manufacturing a new-body Revolve followed by a generic Boolean.
        if shape.kind == "difference":
            target_placement = _portable_placement(target_shape)
            if (
                target_placement is not None
                and isinstance(target_placement.primitive, BoxIR)
            ):
                revolve_cut = _portable_revolve(
                    tool_shape,
                    operation="cut",
                    target=target_placement,
                )
                if revolve_cut is not None:
                    return revolve_cut

        target = _normalize_node(target_shape)
        tool = _normalize_node(tool_shape)
        fillet_cone_join = (
            isinstance(target, FilletIR)
            and shape.kind == "union"
            and isinstance(tool, PlacementIR)
            and isinstance(tool.primitive, ConeIR)
        )
        primitive_boolean = (
            not isinstance(target, FilletIR)
            and (
                isinstance(target, BooleanIR)
                or _portable_csg_placement(target)
            )
            and _portable_csg_placement(tool)
        )
        if fillet_cone_join or primitive_boolean:
            operation = {
                "union": "join",
                "difference": "cut",
                "intersection": "intersect",
            }[shape.kind]
            return BooleanIR(
                operation=operation,
                target=target,
                tool=tool,
            )
        return LegacyShapeIR(shape=shape, source_kind=shape.kind)

    extrude = _portable_extrude(shape)
    if extrude is not None:
        return extrude

    revolve = _portable_revolve(shape)
    if revolve is not None:
        return revolve

    fillet = _portable_fillet(shape)
    if fillet is not None:
        return fillet

    chamfer = _portable_chamfer(shape)
    if chamfer is not None:
        return chamfer

    return LegacyShapeIR(shape=shape, source_kind=shape.kind)


def resolve_feature_ref(root: IRNode, reference: FeatureRefIR) -> IRNode:
    """Resolve one semantic feature path without backend/native identity."""
    if not isinstance(reference, FeatureRefIR):
        raise TypeError("feature reference resolution requires FeatureRefIR")
    if reference.path[0] != "root":
        raise ValueError("FeatureRefIR path must begin at root")

    node = root
    for segment in reference.path[1:]:
        if not isinstance(node, BooleanIR) or segment not in {"target", "tool"}:
            raise ValueError(
                f"FeatureRefIR path segment {segment!r} is not valid for "
                f"{type(node).__name__}"
            )
        node = getattr(node, segment)
    return node


def _boolean_authored_feature_ref(
    design: Shape,
    root: BooleanIR,
    feature: Shape,
    *,
    path: tuple[str, ...] = ("root",),
) -> FeatureRefIR | None:
    """Map authored CSG object identity to typed semantic history roles."""
    if design.kind not in {"union", "difference", "intersection"}:
        return None

    target_shape, tool_shape = design.data
    if feature is tool_shape:
        return FeatureRefIR(path=(*path, "tool"))

    if feature is target_shape and isinstance(
        root.target,
        (PlacementIR, FilletIR),
    ):
        return FeatureRefIR(path=(*path, "target"))

    if isinstance(root.target, BooleanIR):
        nested = _boolean_authored_feature_ref(
            target_shape,
            root.target,
            feature,
            path=(*path, "target"),
        )
        if nested is not None:
            return nested
    return None


def _configuration_feature_ref(
    design: Shape,
    feature: Shape,
    root: IRNode,
) -> FeatureRefIR:
    """Resolve authored identity to semantic IR before native ids exist."""
    # Keep the already-qualified #424 authored Revolve-cut identity stable: the
    # source tool becomes the semantic root feature rather than a Boolean tool.
    if (
        isinstance(root, RevolveIR)
        and root.operation == "cut"
        and design.kind == "difference"
    ):
        _target, authored_tool = design.data
        if feature is not authored_tool:
            raise ValueError(
                "suppression feature is not the authored root Revolve feature"
            )
        return FeatureRefIR(path=("root",))

    if isinstance(root, BooleanIR):
        reference = _boolean_authored_feature_ref(design, root, feature)
        if reference is not None:
            # Resolve immediately so malformed semantic paths fail during
            # frontend normalization rather than in a backend.
            resolve_feature_ref(root, reference)
            return reference
        raise ValueError(
            "suppression feature is not a member of the typed Boolean history"
        )

    raise ValueError(
        "portable suppression requires a qualified semantic feature history"
    )


def _normalize_configuration(configured, root: IRNode) -> ConfigurationIR:
    """Normalize the first suppression-only configuration semantic slice."""
    from .configurations import _SuppressionColumn

    if configured.rules:
        raise ValueError(
            "portable ConfigurationIR does not support configuration rules yet"
        )
    if not configured.columns or any(
        not isinstance(column, _SuppressionColumn)
        for column in configured.columns
    ):
        raise ValueError(
            "portable ConfigurationIR currently supports suppression columns only"
        )

    columns = tuple(
        SuppressionColumnIR(
            feature=_configuration_feature_ref(
                configured.design,
                column.feature,
                root,
            )
        )
        for column in configured.columns
    )
    rows = []
    for name, cells in configured.rows:
        converted = []
        for cell in cells:
            if cell == "true":
                converted.append(True)
            elif cell == "false":
                converted.append(False)
            else:
                raise ValueError(
                    "portable suppression ConfigurationIR requires boolean cells"
                )
        rows.append(
            ConfigurationRowIR(
                name=name,
                cells=tuple(converted),
            )
        )
    return ConfigurationIR(
        active=configured.active,
        columns=columns,
        rows=tuple(rows),
    )


def normalize_configured_design(configured) -> ModelIR | None:
    """Normalize the bounded portable Configure/Suppress slice when qualified.

    Returning None marks configuration authoring that is still outside the
    multi-backend semantic IR migration. Stable SolidCraft may retain its
    existing compatibility path for that surface; experimental backends must
    fail closed rather than interpret it independently.
    """
    from .configurations import _ConfiguredDesign, _SuppressionColumn

    if not isinstance(configured, _ConfiguredDesign):
        raise TypeError(
            "configured Forge IR normalization requires _ConfiguredDesign"
        )
    if not isinstance(configured.design, Shape):
        return None
    if len(configured.columns) != 1:
        return None
    if not isinstance(configured.columns[0], _SuppressionColumn):
        return None

    root = _normalize_node(configured.design)
    if isinstance(root, LegacyShapeIR):
        return None

    return ModelIR(
        root=root,
        parameters=_parameter_ir(configured.design),
        configuration=_normalize_configuration(configured, root),
    )


def normalize_model(value) -> ModelIR:
    """Normalize one Forge authored result into backend-independent semantic IR."""
    from .configurations import _ConfiguredDesign

    if isinstance(value, Shape):
        return ModelIR(
            root=_normalize_node(value),
            parameters=_parameter_ir(value),
        )
    if isinstance(value, _ConfiguredDesign):
        model = normalize_configured_design(value)
        if model is None:
            raise ValueError(
                "configured design is outside the qualified portable IR slice"
            )
        return model
    raise TypeError(
        "Forge IR normalization requires a Shape or configured Shape design"
    )


def normalize_shape(shape: Shape) -> ModelIR:
    """Normalize one Forge Shape into backend-independent semantic IR."""
    if not isinstance(shape, Shape):
        raise TypeError("Forge IR normalization requires a Shape")
    return normalize_model(shape)


def is_portable(model: ModelIR) -> bool:
    """Return whether this model no longer depends on LegacyShapeIR."""
    return not isinstance(model.root, LegacyShapeIR)


__all__ = [
    "AxisLineIR",
    "BooleanIR",
    "BoxIR",
    "ChamferIR",
    "CircleProfileIR",
    "CylinderIR",
    "ConeIR",
    "ExtrudeIR",
    "FaceBoundaryIR",
    "FeatureRefIR",
    "ConfigurationIR",
    "ConfigurationRowIR",
    "SuppressionColumnIR",
    "IRNode",
    "LegacyShapeIR",
    "ModelIR",
    "ParameterIR",
    "PlacementIR",
    "PolygonProfileIR",
    "PrimitiveIR",
    "ProfileIR",
    "RegionIR",
    "RevolveIR",
    "ScalarBinaryIR",
    "ScalarExpressionIR",
    "ScalarLiteralIR",
    "ScalarParameterRefIR",
    "ScalarUnaryIR",
    "SketchIR",
    "SketchCoordinateDimensionIR",
    "SketchLengthDimensionIR",
    "SketchLineIR",
    "SketchOrientationConstraintIR",
    "SketchPointIR",
    "SketchRelationsIR",
    "SphereIR",
    "_polygon_region_interior_point",
    "_region_interior_point",
    "is_portable",
    "normalize_configured_design",
    "normalize_model",
    "normalize_shape",
    "resolve_feature_ref",
]
