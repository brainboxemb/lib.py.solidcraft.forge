"""Primitive placement normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from functools import singledispatch

from ...core import Shape, _dim_add
from ...frontend.primitives import (
    Primitive,
    BoxPrimitive,
    SpherePrimitive,
    CylinderPrimitive,
    ConePrimitive,
)
from ..base import BoxIR, ConeIR, CylinderIR, PlacementIR, SphereIR
from ..body import IRNode


def _anchor_vector(anchor) -> tuple[int, int, int]:
    return tuple(int(value) for value in anchor.vector)


def _shift_point(point, delta):
    return tuple(
        _dim_add(current, added)
        for current, added in zip(point, delta)
    )


@singledispatch
def _primitive_ir(primitive):
    return None


@_primitive_ir.register(BoxPrimitive)
def _box_ir(primitive):
    return BoxIR(
        length=primitive.length,
        width=primitive.width,
        height=primitive.thickness,
    )


@_primitive_ir.register(SpherePrimitive)
def _sphere_ir(primitive):
    return SphereIR(radius=primitive.radius)


@_primitive_ir.register(CylinderPrimitive)
def _cylinder_ir(primitive):
    return CylinderIR(
        height=primitive.height,
        diameter=primitive.diameter,
        axis=primitive.axis.value,
    )


@_primitive_ir.register(ConePrimitive)
def _cone_ir(primitive):
    return ConeIR(
        height=primitive.height,
        diameter=primitive.diameter,
        top_diameter=primitive.top_diameter,
        axis=primitive.axis.value,
    )


def _typed_placement(primitive, point, anchor, *, explicit=False, source_kind="placement"):
    geometry = _primitive_ir(primitive)
    if geometry is None:
        return None
    return PlacementIR(
        primitive=geometry,
        point=point,
        anchor=_anchor_vector(anchor),
        explicit=explicit,
        source_kind=source_kind,
    )


def _legacy_direct_placement(shape):
    """Compatibility for callers that still construct raw Shape(kind, data)."""
    if shape.kind == "box":
        length, width, height, anchor = shape.data
        primitive = BoxIR(length=length, width=width, height=height)
    elif shape.kind == "cylinder":
        height, diameter, axis, anchor = shape.data
        primitive = CylinderIR(height=height, diameter=diameter, axis=axis)
    elif shape.kind == "cone":
        height, diameter, top_diameter, axis, anchor = shape.data
        primitive = ConeIR(
            height=height,
            diameter=diameter,
            top_diameter=top_diameter,
            axis=axis,
        )
    elif shape.kind == "sphere":
        radius, anchor = shape.data
        primitive = SphereIR(radius=radius)
    else:
        return None
    return PlacementIR(
        primitive=primitive,
        point=(0, 0, 0),
        anchor=_anchor_vector(anchor),
    )


def _portable_placement(shape: Shape) -> PlacementIR | None:
    """Normalize typed primitive/placement authoring into semantic IR."""
    if isinstance(shape, Primitive):
        return _typed_placement(
            shape,
            (0, 0, 0),
            shape.anchor,
        )

    if shape.kind == "placed_box":
        box, x, y, z, anchor = shape.data
        if isinstance(box, BoxPrimitive):
            return _typed_placement(
                box,
                (x, y, z),
                anchor,
                explicit=True,
            )
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
        if isinstance(child, (CylinderPrimitive, ConePrimitive)):
            return _typed_placement(
                child,
                (x, y, z),
                child.anchor,
                explicit=True,
            )

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
            source_kind="translated",
        )

    return _legacy_direct_placement(shape)


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
