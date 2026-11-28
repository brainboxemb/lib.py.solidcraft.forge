"""Public primitive authoring constructors and placement helpers."""

from .selectors import Anchor, Axis, _direction_selector
from .scalars import _dim_add, half
from .shape import Shape, feature

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
    diameter. Keep the axial base direct so BOTTOM/LEFT/FRONT anchors do not
    acquire a synthetic height dependency through +height/2 -height/2.
    """
    extents = {
        "X": (height, diameter, diameter),
        "Y": (diameter, height, diameter),
        "Z": (diameter, diameter, height),
    }[axis]
    center = _primitive_center_from_anchor(extents, point, anchor)
    selector = _direction_selector(anchor)
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    base = list(center)
    axial_side = selector.vector[index]
    if axial_side < 0:
        base[index] = point[index]
    elif axial_side > 0:
        base[index] = _dim_add(point[index], -height)
    else:
        base[index] = _dim_add(point[index], -half(height))
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

