"""Public hole-family and plastic-feature authoring constructors."""

from math import isfinite

from .selectors import Anchor, Depth, _AxisRef
from .scalars import _pv, left, right
from .shape import Shape, feature

_HOLE_FIELDS = (
    "type", "diameter", "depth", "direction", "counterbore_diameter",
    "counterbore_depth", "countersink_diameter", "countersink_angle",
    "thread", "hand", "thread_depth", "modeled", "ease_out",
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
