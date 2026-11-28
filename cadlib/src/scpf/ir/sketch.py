"""Sketch, profile, region and sketch-entity semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Any

from ..core import Anchor, _dim_add, _pv as pv
from .base import BodyIR

@dataclass(frozen=True)
class CircleProfileIR:
    """One closed circular 2D profile inside a semantic Sketch."""

    diameter: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "circle"


@dataclass(frozen=True)
class RectangleProfileIR:
    """Dimension-defined rectangle around one semantic sketch-local centre."""

    width: Any
    depth: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "rectangle"

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or isinstance(self.depth, bool)
            or not isfinite(pv(self.width))
            or not isfinite(pv(self.depth))
            or pv(self.width) <= 0
            or pv(self.depth) <= 0
        ):
            raise ValueError(
                "RectangleProfileIR width/depth must be positive CAD dimensions"
            )
        if (
            not isinstance(self.center, tuple)
            or len(self.center) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.center
            )
        ):
            raise ValueError(
                "RectangleProfileIR center must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class RoundedRectangleProfileIR:
    """Rectangle profile whose four corners share one circular radius."""

    width: Any
    depth: Any
    radius: Any
    center: tuple[Any, Any] = (0, 0)
    source_kind: str = "rounded_rectangle"

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or isinstance(self.depth, bool)
            or isinstance(self.radius, bool)
            or not isfinite(pv(self.width))
            or not isfinite(pv(self.depth))
            or not isfinite(pv(self.radius))
            or pv(self.width) <= 0
            or pv(self.depth) <= 0
            or pv(self.radius) <= 0
            or pv(self.radius) * 2 >= min(pv(self.width), pv(self.depth))
        ):
            raise ValueError(
                "RoundedRectangleProfileIR requires positive dimensions and "
                "radius below half the shorter side"
            )
        if (
            not isinstance(self.center, tuple)
            or len(self.center) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.center
            )
        ):
            raise ValueError(
                "RoundedRectangleProfileIR center must contain two finite CAD dimensions"
            )


@dataclass(frozen=True)
class SlotProfileIR:
    """One authored native Slot construction in semantic sketch coordinates."""

    construction: str
    points: tuple[tuple[Any, Any], ...]
    width: Any
    sweep: float | None = None
    offset: tuple[Any, Any] = (0, 0)
    source_kind: str = "slot"

    def __post_init__(self):
        expected = {
            "center_to_center": 2,
            "overall": 2,
            "center_point": 2,
            "arc_three_point": 3,
            "arc_center_end": 3,
            "arc_center_sweep": 2,
        }
        if self.construction not in expected:
            raise ValueError("SlotProfileIR construction is unsupported")
        if (
            not isinstance(self.points, tuple)
            or len(self.points) != expected[self.construction]
            or any(
                not isinstance(point, tuple)
                or len(point) != 2
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in point
                )
                for point in self.points
            )
        ):
            raise ValueError(
                "SlotProfileIR points do not match the construction contract"
            )
        if (
            isinstance(self.width, bool)
            or not isfinite(pv(self.width))
            or pv(self.width) <= 0
        ):
            raise ValueError("SlotProfileIR width must be positive")
        if (
            not isinstance(self.offset, tuple)
            or len(self.offset) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.offset
            )
        ):
            raise ValueError(
                "SlotProfileIR offset must contain two finite CAD dimensions"
            )

        numeric = tuple(
            tuple(float(pv(value)) for value in point)
            for point in self.points
        )
        if self.construction in {
            "center_to_center",
            "overall",
            "center_point",
        }:
            if numeric[0] == numeric[1]:
                raise ValueError("straight SlotProfileIR endpoints must differ")
            if self.construction == "overall":
                if hypot(
                    numeric[1][0] - numeric[0][0],
                    numeric[1][1] - numeric[0][1],
                ) <= pv(self.width):
                    raise ValueError(
                        "overall SlotProfileIR length must exceed width"
                    )
        elif self.construction == "arc_three_point":
            if len(set(numeric)) != 3:
                raise ValueError(
                    "arc-three-point SlotProfileIR points must be distinct"
                )
        else:
            if numeric[0] == numeric[1]:
                raise ValueError(
                    "arc-center SlotProfileIR center and start must differ"
                )
            if self.construction == "arc_center_sweep":
                if (
                    self.sweep is None
                    or isinstance(self.sweep, bool)
                    or not isinstance(self.sweep, (int, float))
                    or not isfinite(self.sweep)
                    or not 0 < self.sweep < 360
                ):
                    raise ValueError(
                        "arc-center SlotProfileIR sweep must be fixed in (0, 360)"
                    )
            elif self.sweep is not None:
                raise ValueError(
                    "arc-center end SlotProfileIR must not also carry sweep"
                )


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


ProfileIR = (
    CircleProfileIR
    | RectangleProfileIR
    | RoundedRectangleProfileIR
    | SlotProfileIR
    | PolygonProfileIR
)


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
class SketchSupportIR:
    """Semantic support of one Sketch on an existing typed body.

    parent is a public Anchor value when the Sketch is attached to a target
    surface. parent=None means the Sketch uses an explicit world frame while
    still modifying target.
    """

    target: BodyIR
    parent: str | None = None

    def __post_init__(self):
        if not isinstance(self.target, BodyIR):
            raise ValueError("SketchSupportIR target must be BodyIR")
        if self.parent is not None and self.parent not in {
            "top", "bottom", "center", "inner_bottom",
        }:
            raise ValueError("SketchSupportIR parent anchor is unsupported")


@dataclass(frozen=True)
class SketchIR:
    """2D sketch geometry plus backend-neutral support/frame semantics."""

    name: str
    plane: PlaneIR
    profiles: tuple[ProfileIR, ...]
    relations: SketchRelationsIR | None = None
    support: SketchSupportIR | None = None
    rotation: tuple[float, float, float] | None = None
    graph: "SketchEntityGraphIR | None" = None
    source_kind: str = "sketch"

    def __post_init__(self):
        if not isinstance(self.plane, PlaneIR):
            raise ValueError("SketchIR plane must be PlaneIR")
        if self.relations is not None and not isinstance(
            self.relations, SketchRelationsIR
        ):
            raise ValueError("SketchIR relations must be SketchRelationsIR")
        if self.support is not None and not isinstance(
            self.support, SketchSupportIR
        ):
            raise ValueError("SketchIR support must be SketchSupportIR")
        if self.rotation is not None:
            if (
                not isinstance(self.rotation, tuple)
                or len(self.rotation) != 3
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                    for value in self.rotation
                )
            ):
                raise ValueError(
                    "SketchIR rotation must be a fixed finite XYZ degree tuple"
                )
        if self.graph is not None and not isinstance(
            self.graph, SketchEntityGraphIR
        ):
            raise ValueError("SketchIR graph must be SketchEntityGraphIR")


@dataclass(frozen=True)
class RegionIR:
    """Closed Sketch region by profile membership or authored local selector."""

    outer: int | None = None
    holes: tuple[int, ...] = ()
    selector: tuple[float, float] | None = None
    exact: bool = False

    def __post_init__(self):
        membership = self.outer is not None
        selected = self.selector is not None
        if membership == selected:
            raise ValueError(
                "RegionIR requires exactly one membership or selector representation"
            )
        if membership:
            if type(self.outer) is not int or self.outer < 0:
                raise ValueError(
                    "RegionIR outer must be a non-negative profile index"
                )
            if (
                not isinstance(self.holes, tuple)
                or any(
                    type(index) is not int or index < 0
                    for index in self.holes
                )
            ):
                raise ValueError(
                    "RegionIR holes must contain non-negative profile indexes"
                )
            if self.outer in self.holes:
                raise ValueError(
                    "RegionIR outer profile cannot also be a hole"
                )
            if len(set(self.holes)) != len(self.holes):
                raise ValueError(
                    "RegionIR hole profile indexes must be unique"
                )
            if self.exact:
                raise ValueError(
                    "membership RegionIR does not need exact selector mode"
                )
            return

        if self.holes:
            raise ValueError("selector RegionIR cannot carry profile holes")
        if (
            not isinstance(self.selector, tuple)
            or len(self.selector) != 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in self.selector
            )
        ):
            raise ValueError(
                "RegionIR selector must be one fixed finite Sketch-local point"
            )
        if not isinstance(self.exact, bool):
            raise ValueError("RegionIR exact must be bool")


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
    if (
        len(sketch.profiles) == 1
        and region.outer == 0
        and not region.holes
        and isinstance(sketch.profiles[0], CircleProfileIR)
    ):
        profile = sketch.profiles[0]
        if (
            isinstance(profile.diameter, bool)
            or not isfinite(pv(profile.diameter))
            or pv(profile.diameter) <= 0
        ):
            raise ValueError("qualified circle diameter must be positive")
        center = tuple(float(pv(value)) for value in profile.center)
        if any(not isfinite(value) for value in center):
            raise ValueError("qualified circle center must be finite")
        return center

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


def _basic_profile_region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    if len(sketch.profiles) != 1 or region.outer != 0 or region.holes:
        raise ValueError(
            "qualified basic profile region requires one outer profile"
        )
    profile = sketch.profiles[0]
    if isinstance(
        profile,
        (RectangleProfileIR, RoundedRectangleProfileIR),
    ):
        return tuple(float(pv(value)) for value in profile.center)
    if not isinstance(profile, SlotProfileIR):
        raise ValueError("profile is not one qualified basic profile")

    def shifted(point):
        return tuple(
            float(pv(_dim_add(value, profile.offset[index])))
            for index, value in enumerate(point)
        )

    points = tuple(shifted(point) for point in profile.points)
    if profile.construction in {"center_to_center", "overall"}:
        return (
            (points[0][0] + points[1][0]) / 2.0,
            (points[0][1] + points[1][1]) / 2.0,
        )
    if profile.construction == "center_point":
        return points[0]
    if profile.construction == "arc_three_point":
        return points[1]
    # The start point lies on the Slot centre-line and strictly inside the
    # finite-width region for both arc-center construction forms.
    return points[1]


def _region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Derive backend transport from semantic profile/region geometry."""
    if region.selector is not None:
        return region.selector

    if (
        0 <= region.outer < len(sketch.profiles)
        and isinstance(sketch.profiles[region.outer], PolygonProfileIR)
    ):
        return _polygon_region_interior_point(sketch, region)
    if (
        0 <= region.outer < len(sketch.profiles)
        and isinstance(sketch.profiles[region.outer], CircleProfileIR)
    ):
        return _circle_region_interior_point(sketch, region)
    return _basic_profile_region_interior_point(sketch, region)

@dataclass(frozen=True)
class SketchChainSegmentIR:
    """One semantic segment in an authored connected Sketch chain."""

    kind: str
    start: tuple[Any, Any]
    end: tuple[Any, Any]
    through: tuple[Any, Any] | None = None
    center: tuple[Any, Any] | None = None
    clockwise: bool | None = None

    def __post_init__(self):
        if self.kind not in {
            "line",
            "arc_tangent",
            "arc_three_point",
            "arc_center_point",
        }:
            raise ValueError("SketchChainSegmentIR kind is unsupported")
        for label, point in (
            ("start", self.start),
            ("end", self.end),
            ("through", self.through),
            ("center", self.center),
        ):
            if point is None:
                continue
            if (
                not isinstance(point, tuple)
                or len(point) != 2
                or any(
                    isinstance(value, bool) or not isfinite(pv(value))
                    for value in point
                )
            ):
                raise ValueError(
                    f"SketchChainSegmentIR {label} must be a finite 2D point"
                )
        if self.kind == "arc_three_point":
            if self.through is None or self.center is not None:
                raise ValueError(
                    "arc_three_point requires through and no center"
                )
        elif self.kind == "arc_center_point":
            if self.center is None or not isinstance(self.clockwise, bool):
                raise ValueError(
                    "arc_center_point requires center and clockwise"
                )
        elif self.through is not None or self.center is not None:
            raise ValueError(
                "line/tangent SketchChainSegmentIR cannot carry arc control points"
            )


@dataclass(frozen=True)
class SketchChainIR:
    """Engine-neutral connected line/arc Sketch chain."""

    name: str
    plane: PlaneIR | None
    segments: tuple[SketchChainSegmentIR, ...]
    closed: bool
    source_kind: str = "sketch_chain"

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("SketchChainIR name must be non-empty")
        if self.plane is not None and not isinstance(self.plane, PlaneIR):
            raise ValueError("SketchChainIR plane must be PlaneIR or None")
        if (
            not isinstance(self.segments, tuple)
            or not self.segments
            or any(
                not isinstance(segment, SketchChainSegmentIR)
                for segment in self.segments
            )
        ):
            raise ValueError("SketchChainIR requires semantic segments")
        if not isinstance(self.closed, bool):
            raise ValueError("SketchChainIR closed must be bool")


@dataclass(frozen=True)
class TextEntityIR:
    """Editable Sketch text independent of support/native ids."""

    text: str
    height: Any
    font: str
    position: tuple[Any, Any] = (0, 0)
    source_kind: str = "text"

    def __post_init__(self):
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("TextEntityIR text must be non-empty")
        if not isinstance(self.font, str) or not self.font.strip():
            raise ValueError("TextEntityIR font must be non-empty")
        if (
            isinstance(self.height, bool)
            or not isfinite(pv(self.height))
            or pv(self.height) <= 0
        ):
            raise ValueError("TextEntityIR height must be positive")
        if (
            not isinstance(self.position, tuple)
            or len(self.position) != 2
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.position
            )
        ):
            raise ValueError(
                "TextEntityIR position must contain two finite CAD dimensions"
            )


SketchGraphEntityIR = ProfileIR | SketchChainIR | TextEntityIR


@dataclass(frozen=True)
class SketchEntityRefIR:
    """Sketch-local semantic source reference for pattern/mirror operations."""

    kind: str
    index: int

    def __post_init__(self):
        if self.kind not in {"entity", "operation"}:
            raise ValueError("SketchEntityRefIR kind must be entity or operation")
        if type(self.index) is not int or self.index < 0:
            raise ValueError("SketchEntityRefIR index must be non-negative")


@dataclass(frozen=True)
class SketchRectangularPatternIR:
    """Native Sketch rectangular-pattern meaning over one semantic source."""

    source: SketchEntityRefIR
    count: Any
    spacing: Any
    direction: tuple[float, float]
    count2: Any = 1
    spacing2: Any | None = None
    direction2: tuple[float, float] | None = None
    alignment: str = "right"
    alignment2: str = "right"
    reversed: bool = False
    reversed2: bool = False
    source_kind: str = "sketch_pattern_rectangular"

    def __post_init__(self):
        if not isinstance(self.source, SketchEntityRefIR):
            raise ValueError(
                "SketchRectangularPatternIR source must be SketchEntityRefIR"
            )
        for value, label in ((self.count, "count"), (self.count2, "count2")):
            concrete = pv(value)
            if (
                isinstance(value, bool)
                or not isfinite(concrete)
                or not 1 <= concrete <= 500
                or not float(concrete).is_integer()
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be 1..500"
                )
        if pv(self.count) * pv(self.count2) > 500:
            raise ValueError(
                "SketchRectangularPatternIR supports at most 500 instances"
            )
        for value, label in (
            (self.spacing, "spacing"),
            (self.spacing2, "spacing2"),
        ):
            if value is not None and (
                isinstance(value, bool) or not isfinite(pv(value))
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be finite"
                )
        for vector, label, optional in (
            (self.direction, "direction", False),
            (self.direction2, "direction2", True),
        ):
            if vector is None and optional:
                continue
            if (
                not isinstance(vector, tuple)
                or len(vector) != 2
                or any(
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not isfinite(component)
                    for component in vector
                )
                or sum(component * component for component in vector) <= 0
            ):
                raise ValueError(
                    f"SketchRectangularPatternIR {label} must be a fixed non-zero 2D vector"
                )
        if self.alignment not in {"left", "center", "right"}:
            raise ValueError("SketchRectangularPatternIR alignment is invalid")
        if self.alignment2 not in {"left", "center", "right"}:
            raise ValueError("SketchRectangularPatternIR alignment2 is invalid")
        if not isinstance(self.reversed, bool) or not isinstance(
            self.reversed2, bool
        ):
            raise ValueError(
                "SketchRectangularPatternIR reversed flags must be bool"
            )


@dataclass(frozen=True)
class SketchMirrorIR:
    """Mirror one semantic Sketch source over a local origin axis."""

    source: SketchEntityRefIR
    axis: str
    source_kind: str = "sketch_mirror"

    def __post_init__(self):
        if not isinstance(self.source, SketchEntityRefIR):
            raise ValueError("SketchMirrorIR source must be SketchEntityRefIR")
        if self.axis not in {"x", "y"}:
            raise ValueError("SketchMirrorIR axis must be x or y")


SketchOperationIR = SketchRectangularPatternIR | SketchMirrorIR


@dataclass(frozen=True)
class SketchEntityGraphIR:
    """Support-independent semantic contents authored inside one Sketch."""

    entities: tuple[SketchGraphEntityIR, ...]
    open_chains: tuple[SketchChainIR, ...] = ()
    operations: tuple[SketchOperationIR, ...] = ()
    source_kind: str = "sketch_entity_graph"

    def __post_init__(self):
        if (
            not isinstance(self.entities, tuple)
            or any(
                not isinstance(
                    entity,
                    (
                        CircleProfileIR,
                        RectangleProfileIR,
                        RoundedRectangleProfileIR,
                        SlotProfileIR,
                        PolygonProfileIR,
                        SketchChainIR,
                        TextEntityIR,
                    ),
                )
                for entity in self.entities
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR entities contain unsupported semantic nodes"
            )
        if any(
            isinstance(entity, SketchChainIR) and not entity.closed
            for entity in self.entities
        ):
            raise ValueError(
                "SketchEntityGraphIR entities require closed SketchChainIR"
            )
        if (
            not isinstance(self.open_chains, tuple)
            or any(
                not isinstance(chain, SketchChainIR) or chain.closed
                for chain in self.open_chains
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR open_chains require open SketchChainIR"
            )
        if (
            not isinstance(self.operations, tuple)
            or any(
                not isinstance(
                    operation,
                    (SketchRectangularPatternIR, SketchMirrorIR),
                )
                for operation in self.operations
            )
        ):
            raise ValueError(
                "SketchEntityGraphIR operations contain unsupported nodes"
            )
        for index, operation in enumerate(self.operations):
            source = operation.source
            if source.kind == "entity":
                if source.index >= len(self.entities):
                    raise ValueError(
                        "Sketch operation references missing semantic entity"
                    )
            elif source.index >= index:
                raise ValueError(
                    "Sketch operation must reference an earlier operation"
                )
