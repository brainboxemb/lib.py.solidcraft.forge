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
from math import hypot, isfinite
from typing import Any

from .core import (
    Anchor,
    Faces,
    Shape,
    _FaceBoundarySelection,
    _dim_add,
    _pv as pv,
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


@dataclass(frozen=True)
class SphereIR:
    """Spherical primitive geometry independent of native diameter spelling."""

    radius: Any
    source_kind: str = "sphere"


PrimitiveIR = BoxIR | CylinderIR | SphereIR


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

    def __post_init__(self):
        if type(self.outer) is not int or self.outer < 0:
            raise ValueError("RegionIR outer must be a non-negative profile index")
        if (
            not isinstance(self.holes, tuple)
            or any(type(index) is not int or index < 0 for index in self.holes)
        ):
            raise ValueError(
                "RegionIR holes must contain non-negative profile indexes"
            )
        if self.outer in self.holes:
            raise ValueError("RegionIR outer profile cannot also be a hole")
        if len(set(self.holes)) != len(self.holes):
            raise ValueError("RegionIR hole profile indexes must be unique")


def _circle_region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Return one deterministic interior point for the qualified circle region.

    The point is derived from semantic profile geometry and is never retained
    as RegionIR intent. Native backends may use it only as a transport selector
    when their command API requires one.
    """
    indexes = (region.outer,) + region.holes
    if any(index >= len(sketch.profiles) for index in indexes):
        raise ValueError("circle region references a missing sketch profile")

    outer = sketch.profiles[region.outer]
    if not isinstance(outer, CircleProfileIR):
        raise ValueError("qualified circle region requires CircleProfileIR profiles")
    if tuple(outer.center) != (0, 0):
        raise ValueError("qualified circle region currently requires origin centers")

    outer_diameter = pv(outer.diameter)
    if not isfinite(outer_diameter) or outer_diameter <= 0:
        raise ValueError("qualified circle region outer diameter must be positive")

    if not region.holes:
        if len(sketch.profiles) != 1:
            raise ValueError(
                "qualified circle region without holes requires one sketch profile"
            )
        return (0.0, 0.0)

    if len(region.holes) != 1 or len(sketch.profiles) != 2:
        raise ValueError(
            "qualified annular circle region requires exactly two profiles"
        )

    inner = sketch.profiles[region.holes[0]]
    if not isinstance(inner, CircleProfileIR):
        raise ValueError("qualified circle region requires CircleProfileIR profiles")
    if tuple(inner.center) != tuple(outer.center):
        raise ValueError("qualified annular circle region requires concentric profiles")

    inner_diameter = pv(inner.diameter)
    if not isfinite(inner_diameter) or inner_diameter <= 0:
        raise ValueError("qualified circle region inner diameter must be positive")
    if outer_diameter <= inner_diameter:
        raise ValueError(
            "qualified annular circle region requires outer diameter above inner"
        )

    # Midway between the two radii is strictly inside the annular region.
    return ((outer_diameter + inner_diameter) / 4.0, 0.0)


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
class BooleanIR:
    """Bounded recursive primitive CSG intent.

    target may be another BooleanIR so a left-associated public CSG expression
    remains one semantic tree. tool is deliberately one placed primitive in
    the current qualified slice; more general boolean operands stay legacy.
    """

    operation: str
    target: "PlacementIR | BooleanIR"
    tool: PlacementIR
    source_kind: str = "boolean"

    def __post_init__(self):
        if self.operation not in {"join", "cut", "intersect"}:
            raise ValueError(
                "BooleanIR operation must be join, cut or intersect"
            )


@dataclass(frozen=True)
class LegacyShapeIR:
    """Transitional wrapper for stable SolidCraft surface not migrated yet."""

    shape: Shape
    source_kind: str


IRNode = (
    PlacementIR
    | ExtrudeIR
    | ChamferIR
    | BooleanIR
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

    if shape.kind == "sphere":
        radius, anchor = shape.data
        anchor_vector = _anchor_vector(anchor)
        if anchor_vector != (0, 0, 0):
            return None
        return PlacementIR(
            primitive=SphereIR(radius=radius),
            point=(0, 0, 0),
            anchor=anchor_vector,
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
        if placement is None or isinstance(placement.primitive, SphereIR):
            return None
        return PlacementIR(
            primitive=placement.primitive,
            point=_shift_point(placement.point, delta),
            anchor=placement.anchor,
            explicit=True,
        )

    return None


def _portable_extrude(shape: Shape) -> ExtrudeIR | None:
    """Normalize the qualified standalone circle Sketch + Extrude slices."""
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
    if direction not in ("positive", "negative"):
        return None
    if len(profiles) not in (1, 2):
        return None

    semantic_profiles = []
    for profile, profile_anchor, offset in profiles:
        if profile.kind != "circle":
            return None
        if profile_anchor is not Anchor.CENTER:
            return None
        if tuple(offset) != (0, 0):
            return None
        (diameter,) = profile.data
        semantic_profiles.append(CircleProfileIR(diameter=diameter))

    sketch = SketchIR(
        name=sketch_name,
        plane=plane,
        profiles=tuple(semantic_profiles),
    )

    if len(semantic_profiles) == 1:
        if profile_picks is not None or exact_regions:
            return None
        regions = (RegionIR(outer=0),)
    else:
        if not exact_regions or profile_picks is None or len(profile_picks) != 1:
            return None

        diameters = tuple(pv(profile.diameter) for profile in semantic_profiles)
        if (
            any(not isfinite(value) or value <= 0 for value in diameters)
            or diameters[0] == diameters[1]
        ):
            return None

        outer_index = 0 if diameters[0] > diameters[1] else 1
        inner_index = 1 - outer_index
        region = RegionIR(outer=outer_index, holes=(inner_index,))

        try:
            _circle_region_interior_point(sketch, region)
        except ValueError:
            return None

        pick_radius = hypot(*profile_picks[0])
        inner_radius = diameters[inner_index] / 2.0
        outer_radius = diameters[outer_index] / 2.0
        if not inner_radius < pick_radius < outer_radius:
            return None
        regions = (region,)

    return ExtrudeIR(
        sketch=sketch,
        regions=regions,
        distance=distance,
        direction=direction,
    )

def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    if shape.kind != "chamfer":
        return None

    if len(shape.data) == 3:
        # Compatibility with the pre-#271 equal-distance frontend payload.
        base, distance, edges = shape.data
        distance2 = None
        flip = False
    elif len(shape.data) == 5:
        base, distance, edges, distance2, flip = shape.data
    else:
        return None

    # #271 extends stable SolidCraft authoring with two-distance chamfer.
    # That surface is not yet a qualified portable IR capability: keep it
    # behind LegacyShapeIR so SolidCraft retains the native product behavior
    # while Mitcad fails closed instead of guessing asymmetric semantics.
    if distance2 is not None or flip:
        return None

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

    if shape.kind in {"union", "difference", "intersection"}:
        target_shape, tool_shape = shape.data
        target = _normalize_node(target_shape)
        tool = _normalize_node(tool_shape)
        if (
            isinstance(target, (PlacementIR, BooleanIR))
            and isinstance(tool, PlacementIR)
            and isinstance(tool.primitive, (BoxIR, CylinderIR, SphereIR))
        ):
            operation = {
                "union": "join",
                "difference": "cut",
                "intersection": "intersect",
            }[shape.kind]
            return BooleanIR(
                operation=operation,
                target=target,
                tool=tool,
            )
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
    "BooleanIR",
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
    "SphereIR",
    "is_portable",
    "normalize_shape",
]
