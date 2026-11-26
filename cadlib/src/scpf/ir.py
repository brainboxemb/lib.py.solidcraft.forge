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
from typing import Any

from .core import (
    Anchor,
    Faces,
    Shape,
    _FaceBoundarySelection,
    _dim_add,
    parameters_in,
)


@dataclass(frozen=True)
class ParameterIR:
    """One named editable Forge CAD parameter."""

    name: str
    value: float
    unit: str = "mm"


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


PrimitiveIR = BoxIR | CylinderIR


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


ProfileIR = CircleProfileIR


@dataclass(frozen=True)
class SketchIR:
    """Standalone 2D sketch geometry independent of downstream features."""

    name: str
    plane: str
    profiles: tuple[ProfileIR, ...]
    source_kind: str = "sketch"


@dataclass(frozen=True)
class RegionIR:
    """Closed sketch region described by semantic profile membership."""

    outer: int
    holes: tuple[int, ...] = ()


@dataclass(frozen=True)
class ExtrudeIR:
    """Distance extrusion over semantic Sketch regions."""

    sketch: SketchIR
    regions: tuple[RegionIR, ...]
    distance: Any
    direction: str
    source_kind: str = "sketch_base_extrusion"


@dataclass(frozen=True)
class FaceBoundaryIR:
    """Semantic request for all boundary edges of cardinal planar faces."""

    faces: tuple[str, ...]


@dataclass(frozen=True)
class ChamferIR:
    """Equal-distance chamfer over semantic edge-selection intent."""

    base: PlacementIR
    distance: Any
    edges: FaceBoundaryIR
    source_kind: str = "chamfer"


@dataclass(frozen=True)
class BooleanSubtractIR:
    """Qualified subtractive boolean between typed semantic solids."""

    target: PlacementIR
    tool: PlacementIR
    source_kind: str = "difference"


@dataclass(frozen=True)
class LegacyShapeIR:
    """Transitional wrapper for stable SolidCraft surface not migrated yet."""

    shape: Shape
    source_kind: str


IRNode = (
    PlacementIR
    | ExtrudeIR
    | ChamferIR
    | BooleanSubtractIR
    | LegacyShapeIR
)


@dataclass(frozen=True)
class ModelIR:
    """One normalized Forge model independent of a native CAD backend."""

    root: IRNode
    parameters: tuple[ParameterIR, ...]


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


def _parameter_ir(shape: Shape) -> tuple[ParameterIR, ...]:
    return tuple(
        ParameterIR(name, value)
        for name, value in _collect_parameters(shape).items()
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
        if child.kind != "cylinder":
            return None
        height, diameter, axis, anchor = child.data
        return PlacementIR(
            primitive=CylinderIR(
                height=height,
                diameter=diameter,
                axis=axis,
            ),
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


def _portable_extrude(shape: Shape) -> ExtrudeIR | None:
    """Normalize the first qualified standalone Sketch + Extrude slice."""
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
    if operations:
        return None
    if profile_picks is not None or exact_regions:
        return None
    if len(profiles) != 1:
        return None
    if direction not in ("positive", "negative"):
        return None

    profile, profile_anchor, offset = profiles[0]
    if profile.kind != "circle":
        return None
    if profile_anchor is not Anchor.CENTER:
        return None
    if tuple(offset) != (0, 0):
        return None

    (diameter,) = profile.data
    sketch = SketchIR(
        name=sketch_name,
        plane=plane,
        profiles=(CircleProfileIR(diameter=diameter),),
    )
    return ExtrudeIR(
        sketch=sketch,
        regions=(RegionIR(outer=0),),
        distance=distance,
        direction=direction,
    )


def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    if shape.kind != "chamfer":
        return None

    base, distance, edges = shape.data
    base_ir = _portable_placement(base)
    if (
        base_ir is None
        or not isinstance(base_ir.primitive, BoxIR)
        or not isinstance(edges, _FaceBoundarySelection)
        or len(edges.faces) != 1
    ):
        return None

    return ChamferIR(
        base=base_ir,
        distance=distance,
        edges=FaceBoundaryIR(
            tuple(Faces(face).value for face in edges.faces)
        ),
    )


def _normalize_node(shape: Shape) -> IRNode:
    placement = _portable_placement(shape)
    if placement is not None:
        return placement

    if shape.kind == "difference":
        target_shape, tool_shape = shape.data
        target = _normalize_node(target_shape)
        tool = _normalize_node(tool_shape)
        if (
            isinstance(target, PlacementIR)
            and isinstance(target.primitive, BoxIR)
            and isinstance(tool, PlacementIR)
            and isinstance(tool.primitive, CylinderIR)
        ):
            return BooleanSubtractIR(target=target, tool=tool)
        return LegacyShapeIR(shape=shape, source_kind=shape.kind)

    extrude = _portable_extrude(shape)
    if extrude is not None:
        return extrude

    chamfer = _portable_chamfer(shape)
    if chamfer is not None:
        return chamfer

    return LegacyShapeIR(shape=shape, source_kind=shape.kind)


def normalize_shape(shape: Shape) -> ModelIR:
    """Normalize one Forge Shape into backend-independent semantic IR."""
    if not isinstance(shape, Shape):
        raise TypeError("Forge IR normalization requires a Shape")
    return ModelIR(
        root=_normalize_node(shape),
        parameters=_parameter_ir(shape),
    )


def is_portable(model: ModelIR) -> bool:
    """Return whether this model no longer depends on LegacyShapeIR."""
    return not isinstance(model.root, LegacyShapeIR)


__all__ = [
    "BooleanSubtractIR",
    "BoxIR",
    "ChamferIR",
    "CircleProfileIR",
    "CylinderIR",
    "ExtrudeIR",
    "FaceBoundaryIR",
    "IRNode",
    "LegacyShapeIR",
    "ModelIR",
    "ParameterIR",
    "PlacementIR",
    "PrimitiveIR",
    "ProfileIR",
    "RegionIR",
    "SketchIR",
    "is_portable",
    "normalize_shape",
]
