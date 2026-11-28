"""Public 2D profile authoring constructors."""

from ..core import (
    Edges,
    Expression,
    Parameter,
    Shape,
    _pv,
    feature,
    half,
    left,
    right,
)

def Text2D(text, *, height=6.0, font="DejaVu Sans Bold"):
    """Editable sketch lettering (height is capital height, in mm)."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text2D requires non-empty text")
    if not isinstance(font, str) or not font.strip():
        raise ValueError("Text2D requires a font family")
    if _pv(height) <= 0:
        raise ValueError("Text2D height must be positive")
    from ..explicit_sketch import register_profile
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
    from ..explicit_sketch import register_profile
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
    from ..explicit_sketch import register_profile
    return register_profile(Shape("rounded_rectangle", (width, depth, radius)))

def _slot_point(name, value, *, allow_symbolic=False):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{name} must be an (x, y) point")
    point = tuple(value)
    concrete = tuple(_pv(coordinate) for coordinate in point)
    if not all(isfinite(coordinate) for coordinate in concrete):
        raise ValueError(f"{name} must contain finite coordinates")
    # SolidCraft 0.45 direct Slot point fields are numeric PlainPoint values.
    # Straight-Slot constructors may retain symbolic authored intent here so
    # feature lowering can emit numeric seed points plus native dimensions and
    # constraints. Arc-Slot point fields remain direct/fixed in this slice.
    if (
        not allow_symbolic
        and any(
            isinstance(coordinate, (Parameter, Expression))
            for coordinate in point
        )
    ):
        raise TypeError(f"{name} currently requires fixed numeric coordinates")
    return point

def _slot_points_equal(left, right):
    """Compare current Slot point values without discarding symbolic intent."""

    return all(_pv(a) == _pv(b) for a, b in zip(left, right))

def _slot_width(width):
    """Validate one SolidCraft 0.45 native Slot width without baking it."""

    if isinstance(width, bool):
        raise TypeError("slot width must be a numeric CAD dimension")
    try:
        concrete = _pv(width)
    except TypeError as exc:
        raise TypeError("slot width must be a numeric CAD dimension") from exc
    if not isfinite(concrete) or concrete <= 0:
        raise ValueError("slot width must be a positive finite number")
    return width

def SlotCenterToCenter2D(p0, p1, width):
    """Create a straight Slot from the centres of its two round ends.

    Parameters:
        p0: Centre of the first round end as (x, y) in sketch coordinates, in mm.
            Coordinates may be numeric or Parameter/Expression values.
        p1: Centre of the second round end as (x, y) in sketch coordinates, in mm.
            Coordinates may be numeric or Parameter/Expression values.
        width: Total Slot width in mm, numeric or Parameter/Expression. This is
            also the diameter of each round end.

    Limits:
        p0 and p1 must be different points. Parameterized endpoints currently
        require a horizontal or vertical Slot and matching symbolic intent on
        the perpendicular coordinate. Fixed numeric diagonal Slots remain
        supported.

    Example:
        SlotCenterToCenter2D((-10, 0), (10, 0), 6)
    """
    p0 = _slot_point("p0", p0, allow_symbolic=True)
    p1 = _slot_point("p1", p1, allow_symbolic=True)
    if _slot_points_equal(p0, p1):
        raise ValueError("center-to-center Slot endpoints must differ")
    from ..explicit_sketch import register_profile
    return register_profile(
        Shape("slot_center_to_center", (p0, p1, _slot_width(width)))
    )

def SlotOverall2D(p0, p1, width):
    """Create a straight Slot from its two outermost end points.

    Parameters:
        p0: Outermost point of the first round end as (x, y) in sketch coordinates,
            in mm. Coordinates may be numeric or Parameter/Expression values.
        p1: Outermost point of the second round end as (x, y) in sketch coordinates,
            in mm. Coordinates may be numeric or Parameter/Expression values.
        width: Total Slot width in mm, numeric or Parameter/Expression. This is
            also the diameter of each round end.

    Limits:
        The distance from p0 to p1 is the total Slot length, including both
        round ends, and must be larger than width. Parameterized endpoints
        currently require a horizontal or vertical Slot and matching symbolic
        intent on the perpendicular coordinate.

    Example:
        SlotOverall2D((-15, 0), (15, 0), 6)
    """
    p0 = _slot_point("p0", p0, allow_symbolic=True)
    p1 = _slot_point("p1", p1, allow_symbolic=True)
    width = _slot_width(width)
    length = sum((_pv(b) - _pv(a)) ** 2 for a, b in zip(p0, p1)) ** 0.5
    if length <= _pv(width):
        raise ValueError("overall Slot length must be larger than its width")
    from ..explicit_sketch import register_profile
    return register_profile(Shape("slot_overall", (p0, p1, width)))

def SlotCenterPoint2D(center, end, width):
    """Create a straight Slot from its centre and one round-end centre.

    Parameters:
        center: Centre of the complete Slot as (x, y) in sketch coordinates, in mm.
            Coordinates may be numeric or Parameter/Expression values.
        end: Centre of one round end as (x, y) in sketch coordinates, in mm.
            Coordinates may be numeric or Parameter/Expression values.
        width: Total Slot width in mm, numeric or Parameter/Expression. This is
            also the diameter of each round end.

    Limits:
        center and end must differ. The other round-end centre is mirrored
        through center. Parameterized endpoints currently require a horizontal
        or vertical Slot.

    Example:
        SlotCenterPoint2D((0, 0), (10, 0), 6)
    """
    center = _slot_point("center", center, allow_symbolic=True)
    end = _slot_point("end", end, allow_symbolic=True)
    if _slot_points_equal(center, end):
        raise ValueError("center-point Slot end must differ from its centre")
    from ..explicit_sketch import register_profile
    return register_profile(
        Shape("slot_center_point", (center, end, _slot_width(width)))
    )

def SlotArcThreePoint2D(start, through, end, width):
    """Create a curved Slot whose centre arc passes through three points.

    Parameters:
        start: Start point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        through: A point that the centre arc must pass through, as (x, y) in mm.
        end: End point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm, numeric or Parameter/Expression, measured
            perpendicular to the centre arc.

    Limits:
        start, through and end must be three different fixed numeric points.
        Arc-Slot authored points are not parameterized in this release.

    Example:
        SlotArcThreePoint2D((-15, 0), (0, 10), (15, 0), 6)
    """
    start = _slot_point("start", start)
    through = _slot_point("through", through)
    end = _slot_point("end", end)
    if len({start, through, end}) != 3:
        raise ValueError("three-point arc Slot requires three distinct points")
    from ..explicit_sketch import register_profile
    return register_profile(
        Shape("slot_arc_three_point", (start, through, end, _slot_width(width)))
    )

def SlotArcCenter2D(center, start, width, *, end=None, sweep=None):
    """Create a curved Slot from an arc centre and start point.

    Parameters:
        center: Centre of the underlying circular arc as (x, y) in sketch coordinates, in mm.
        start: Start point of the Slot centre arc as (x, y) in sketch coordinates, in mm.
        width: Total Slot width in mm, numeric or Parameter/Expression, measured
            perpendicular to the centre arc.
        end: Optional fixed numeric end point of the centre arc as (x, y) in mm.
        sweep: Optional positive sweep angle in degrees.

    Limits:
        Supply exactly one of end= or sweep=. center, start and end are fixed
        numeric authored points in this release. center and start must differ.
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
    from ..explicit_sketch import register_profile
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
    from ..explicit_sketch import register_profile
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
    from ..explicit_sketch import register_profile
    return register_profile(Shape("polygon", (coordinates, plane, ids)))
