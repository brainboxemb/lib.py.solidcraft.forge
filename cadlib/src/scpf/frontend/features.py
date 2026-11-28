"""Public hole-family and plastic-feature authoring constructors."""

from math import isfinite

from ..core import (
    Anchor,
    Depth,
    Shape,
    _AxisRef,
    _pv,
    feature,
    left,
    right,
)

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

def CountersinkHole(
    *,
    d,
    countersink_d,
    countersink_angle=90,
    depth=Depth.THROUGH_ALL,
    direction=None,

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
