"""Public primitive authoring constructors and typed primitive objects."""

from dataclasses import FrozenInstanceError

from .selectors import Anchor, Axis, _direction_selector
from .scalars import _dim_add, half
from .shape import Shape, feature


def _box_corner_from_anchor(length, width, height, point, anchor):
    """Return a Box minimum corner when one box anchor is placed at point."""
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
    """Resolve a primitive center from an anchor on its world XYZ bounds."""
    vector = _direction_selector(anchor).vector
    return tuple(
        _dim_add(
            coordinate,
            half(extent) if side < 0 else -half(extent) if side > 0 else 0,
        )
        for coordinate, extent, side in zip(point, extents, vector)
    )


def _cylinder_base_from_anchor(height, diameter, axis, point, anchor):
    """Resolve a cylinder axial base point from one world-space anchor."""
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
    """Resolve a cone/frustum base point from an unambiguous axial anchor."""
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
    """Resolve a sphere center from one tangent/center anchor."""
    vector = _direction_selector(anchor).vector
    return tuple(
        _dim_add(
            coordinate,
            radius if side < 0 else -radius if side > 0 else 0,
        )
        for coordinate, side in zip(point, vector)
    )


class Primitive(Shape):
    """Typed reusable primitive Shape.

    Named attributes and primitive methods are the frontend semantic contract.
    Shape.kind/data remain a compatibility snapshot for legacy compiler paths.
    """

    def __setattr__(self, name, value):
        raise FrozenInstanceError(f"cannot assign to field {name!r}")

    def _alignment_center(self):
        return self._center_at((0, 0, 0))

    def _center_at(self, point):
        raise NotImplementedError

    def _with_anchor(self, anchor):
        raise NotImplementedError

    def _place_at_coordinates(self, x, y, z, anchor):
        raise NotImplementedError


class BoxPrimitive(Primitive):
    def __init__(self, length, width, thickness, anchor):
        selector = _direction_selector(anchor)
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "thickness", thickness)
        object.__setattr__(self, "anchor", selector)
        super().__init__("box", (length, width, thickness, selector))

    def _center_at(self, point):
        return _primitive_center_from_anchor(
            (self.length, self.width, self.thickness),
            point,
            self.anchor,
        )

    def _corner_at(self, point):
        return _box_corner_from_anchor(
            self.length,
            self.width,
            self.thickness,
            point,
            self.anchor,
        )

    def _with_anchor(self, anchor):
        return BoxPrimitive(self.length, self.width, self.thickness, anchor)

    def _place_at_coordinates(self, x, y, z, anchor):
        selector = _direction_selector(anchor)
        return Shape("placed_box", (self, x, y, z, selector))


class SpherePrimitive(Primitive):
    def __init__(self, radius, anchor):
        selector = _direction_selector(anchor)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "anchor", selector)
        super().__init__("sphere", (radius, selector))

    def _center_at(self, point):
        return _sphere_center_from_anchor(self.radius, point, self.anchor)

    def _with_anchor(self, anchor):
        return SpherePrimitive(self.radius, anchor)

    def _place_at_coordinates(self, x, y, z, anchor):
        placed = self._with_anchor(anchor)
        return Shape("translated", (placed, (x, y, z)))


class CylinderPrimitive(Primitive):
    def __init__(self, *, diameter, height, axis, anchor):
        try:
            axis = Axis(axis)
        except ValueError as exc:
            raise ValueError(
                "Cylinder axis must be Axis.X, Axis.Y or Axis.Z"
            ) from exc
        selector = _direction_selector(anchor)
        object.__setattr__(self, "diameter", diameter)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "anchor", selector)
        super().__init__(
            "cylinder",
            (height, diameter, axis.value, selector),
        )

    def _center_at(self, point):
        extents = {
            Axis.X: (self.height, self.diameter, self.diameter),
            Axis.Y: (self.diameter, self.height, self.diameter),
            Axis.Z: (self.diameter, self.diameter, self.height),
        }[self.axis]
        return _primitive_center_from_anchor(extents, point, self.anchor)

    def _base_at(self, point):
        return _cylinder_base_from_anchor(
            self.height,
            self.diameter,
            self.axis.value,
            point,
            self.anchor,
        )

    def _with_anchor(self, anchor):
        return CylinderPrimitive(
            diameter=self.diameter,
            height=self.height,
            axis=self.axis,
            anchor=anchor,
        )

    def _place_at_coordinates(self, x, y, z, anchor):
        placed = self._with_anchor(anchor)
        return Shape("placed3d", (placed, x, y, z))


class ConePrimitive(Primitive):
    def __init__(self, *, diameter, top_diameter, height, axis, anchor):
        try:
            axis = Axis(axis)
        except ValueError as exc:
            raise ValueError(
                "Cone axis must be Axis.X, Axis.Y or Axis.Z"
            ) from exc
        selector = _direction_selector(anchor)
        _cone_base_from_anchor(height, axis.value, (0, 0, 0), selector)
        object.__setattr__(self, "diameter", diameter)
        object.__setattr__(self, "top_diameter", top_diameter)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "anchor", selector)
        super().__init__(
            "cone",
            (height, diameter, top_diameter, axis.value, selector),
        )

    def _base_at(self, point):
        return _cone_base_from_anchor(
            self.height,
            self.axis.value,
            point,
            self.anchor,
        )

    def _center_at(self, point):
        base = list(self._base_at(point))
        index = {Axis.X: 0, Axis.Y: 1, Axis.Z: 2}[self.axis]
        base[index] = _dim_add(base[index], half(self.height))
        return tuple(base)

    def _with_anchor(self, anchor):
        return ConePrimitive(
            diameter=self.diameter,
            top_diameter=self.top_diameter,
            height=self.height,
            axis=self.axis,
            anchor=anchor,
        )

    def _place_at_coordinates(self, x, y, z, anchor):
        placed = self._with_anchor(anchor)
        return Shape("placed3d", (placed, x, y, z))


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
    return BoxPrimitive(length, width, thickness, anchor)


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
    return SpherePrimitive(radius, anchor)


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
    return CylinderPrimitive(
        diameter=d,
        height=h,
        axis=axis,
        anchor=anchor,
    )


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
    return ConePrimitive(
        diameter=d,
        top_diameter=top_d,
        height=h,
        axis=axis,
        anchor=anchor,
    )
