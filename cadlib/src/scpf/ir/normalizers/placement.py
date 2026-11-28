"""Primitive placement normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from ...core import Shape, _dim_add
from ..base import BoxIR, ConeIR, CylinderIR, PlacementIR, SphereIR
from ..body import IRNode

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
            source_kind="translated",
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
