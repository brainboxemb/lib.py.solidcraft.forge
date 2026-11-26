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
    Expression,
    Faces,
    Parameter,
    Shape,
    _FaceBoundarySelection,
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
    """Axis-aligned box semantic intent."""

    length: Any
    width: Any
    height: Any
    anchor: tuple[int, int, int]
    source_kind: str = "box"


@dataclass(frozen=True)
class CylinderIR:
    """Principal-axis cylinder semantic intent."""

    height: Any
    diameter: Any
    axis: str
    anchor: tuple[int, int, int]
    point: tuple[Any, Any, Any] = (0, 0, 0)
    source_kind: str = "cylinder"


@dataclass(frozen=True)
class CircleExtrudeIR:
    """One standalone circular sketch extruded by a signed direction."""

    sketch_name: str
    plane: str
    diameter: Any
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

    base: BoxIR
    distance: Any
    edges: FaceBoundaryIR
    source_kind: str = "chamfer"


@dataclass(frozen=True)
class BooleanSubtractIR:
    """Qualified subtractive boolean between typed semantic solids."""

    target: BoxIR
    tool: CylinderIR
    source_kind: str = "difference"


@dataclass(frozen=True)
class LegacyShapeIR:
    """Transitional wrapper for stable SolidCraft surface not migrated yet."""

    shape: Shape
    source_kind: str


IRNode = (
    BoxIR
    | CylinderIR
    | CircleExtrudeIR
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


def _portable_cylinder(shape: Shape) -> CylinderIR | None:
    if shape.kind != "cylinder":
        return None
    height, diameter, axis, anchor = shape.data
    return CylinderIR(
        height=height,
        diameter=diameter,
        axis=axis,
        anchor=tuple(int(value) for value in anchor.vector),
    )


def _portable_circle_extrude(shape: Shape) -> CircleExtrudeIR | None:
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
    return CircleExtrudeIR(
        sketch_name=sketch_name,
        plane=plane,
        diameter=diameter,
        distance=distance,
        direction=direction,
    )


def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    if shape.kind != "chamfer":
        return None

    base, distance, edges = shape.data
    if base.kind != "box":
        return None
    if not isinstance(edges, _FaceBoundarySelection):
        return None
    if len(edges.faces) != 1:
        return None

    base_ir = _normalize_node(base)
    if not isinstance(base_ir, BoxIR):
        return None

    return ChamferIR(
        base=base_ir,
        distance=distance,
        edges=FaceBoundaryIR(
            tuple(Faces(face).value for face in edges.faces)
        ),
    )


def _normalize_node(shape: Shape) -> IRNode:
    if shape.kind == "box":
        length, width, height, anchor = shape.data
        return BoxIR(
            length=length,
            width=width,
            height=height,
            anchor=tuple(int(value) for value in anchor.vector),
        )

    cylinder = _portable_cylinder(shape)
    if cylinder is not None:
        return cylinder

    if shape.kind == "difference":
        target_shape, tool_shape = shape.data
        target = _normalize_node(target_shape)
        tool = _normalize_node(tool_shape)
        if isinstance(target, BoxIR) and isinstance(tool, CylinderIR):
            return BooleanSubtractIR(target=target, tool=tool)
        return LegacyShapeIR(shape=shape, source_kind=shape.kind)

    circle_extrude = _portable_circle_extrude(shape)
    if circle_extrude is not None:
        return circle_extrude

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
    "CylinderIR",
    "CircleExtrudeIR",
    "FaceBoundaryIR",
    "IRNode",
    "LegacyShapeIR",
    "ModelIR",
    "ParameterIR",
    "is_portable",
    "normalize_shape",
]
