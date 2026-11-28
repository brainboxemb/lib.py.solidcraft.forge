"""Profile and region normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from math import hypot, isfinite

from ...core import Anchor, Shape, _dim_add, _pv as pv
from ..profiles import (
    CircleProfileIR,
    PolygonProfileIR,
    ProfileIR,
    RectangleProfileIR,
    RegionIR,
    RoundedRectangleProfileIR,
    SlotProfileIR,
)
from ..sketch import SketchIR, TextEntityIR

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

def _profile_ir_from_shape(
    profile: Shape,
    profile_anchor,
    offset,
    plane: str,
) -> ProfileIR | None:
    try:
        offset = tuple(offset)
        if len(offset) != 2:
            return None

        if profile.kind == "circle":
            if profile_anchor is not Anchor.CENTER:
                return None
            (diameter,) = profile.data
            return CircleProfileIR(
                diameter=diameter,
                center=offset,
            )

        if profile.kind == "rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth = profile.data
            return RectangleProfileIR(
                width=width,
                depth=depth,
                center=offset,
            )

        if profile.kind == "rounded_rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth, radius = profile.data
            return RoundedRectangleProfileIR(
                width=width,
                depth=depth,
                radius=radius,
                center=offset,
            )

        if profile.kind == "polygon":
            if profile_anchor is not None:
                return None
            points, profile_plane, ids = profile.data
            if profile_plane != plane:
                return None
            shifted = tuple(
                tuple(
                    _dim_add(value, offset[index])
                    for index, value in enumerate(point)
                )
                for point in points
            )
            return PolygonProfileIR(
                points=shifted,
                segment_ids=tuple(ids) if ids is not None else None,
            )

        if profile_anchor is not None:
            return None

        if profile.kind == "slot_center_to_center":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="center_to_center",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_overall":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="overall",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_center_point":
            center, end, width = profile.data
            return SlotProfileIR(
                construction="center_point",
                points=(tuple(center), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_three_point":
            start, through, end, width = profile.data
            return SlotProfileIR(
                construction="arc_three_point",
                points=(tuple(start), tuple(through), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_center":
            center, start, end, sweep, width = profile.data
            if end is not None:
                return SlotProfileIR(
                    construction="arc_center_end",
                    points=(tuple(center), tuple(start), tuple(end)),
                    width=width,
                    offset=offset,
                )
            return SlotProfileIR(
                construction="arc_center_sweep",
                points=(tuple(center), tuple(start)),
                width=width,
                sweep=float(sweep),
                offset=offset,
            )
    except (TypeError, ValueError):
        return None

    return None

def _extrude_regions(
    sketch: SketchIR,
    profile_picks,
    exact_regions,
) -> tuple[RegionIR, ...] | None:
    """Normalize public all-region or point-selected region intent.

    Existing directly-resolvable concentric/polygon families retain stronger
    semantic boundary membership. General picks remain authored selector intent.
    """
    if profile_picks is not None:
        if not isinstance(profile_picks, (tuple, list)):
            return None

        # A single explicitly selected profile remains explicit selector intent
        # so the native command preserves its authored profiles=[...] spelling.
        if len(sketch.profiles) == 1:
            try:
                return tuple(
                    RegionIR(
                        selector=tuple(float(value) for value in point),
                        exact=exact_regions,
                    )
                    for point in profile_picks
                )
            except (TypeError, ValueError):
                return None

        # Preserve the already-qualified stronger membership model only when
        # the source really is the bounded concentric-circle family.
        concentric = (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and sketch.profiles
            and all(
                isinstance(profile, CircleProfileIR)
                for profile in sketch.profiles
            )
            and len(sketch.profiles) == len(sketch.graph.entities)
        )
        if concentric:
            try:
                _circle_profile_radii(sketch)
            except ValueError:
                concentric = False

        if concentric:
            try:
                return tuple(
                    _concentric_circle_region_from_pick(sketch, point)
                    for point in profile_picks
                )
            except ValueError:
                return None

        # Preserve exact single-polygon membership for the older qualified
        # profile contract (normally reached above only if graph/profile
        # composition changes later).
        if (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and len(sketch.profiles) == 1
            and isinstance(sketch.profiles[0], PolygonProfileIR)
            and len(profile_picks) == 1
        ):
            try:
                return (
                    _polygon_region_from_exact_pick(
                        sketch,
                        profile_picks[0],
                    ),
                )
            except ValueError:
                return None

        try:
            return tuple(
                RegionIR(
                    selector=tuple(float(value) for value in point),
                    exact=exact_regions,
                )
                for point in profile_picks
            )
        except (TypeError, ValueError):
            return None

    if exact_regions:
        return None

    if (
        sketch.graph is not None
        and not sketch.graph.operations
        and len(sketch.profiles) == 1
        and len(sketch.graph.entities) == 1
        and not isinstance(sketch.graph.entities[0], TextEntityIR)
    ):
        try:
            region = RegionIR(outer=0)
            _region_interior_point(sketch, region)
            return (region,)
        except ValueError:
            pass
    return ()
