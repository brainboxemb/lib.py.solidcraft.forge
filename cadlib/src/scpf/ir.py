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


@dataclass(frozen=True)
class PolygonProfileIR:
    """One closed straight-segment profile in Sketch-local coordinates."""

    points: tuple[tuple[Any, Any], ...]
    segment_ids: tuple[str, ...] | None = None
    source_kind: str = "polygon"

    def __post_init__(self):
        if (
            not isinstance(self.points, tuple)
            or len(self.points) < 3
            or any(
                not isinstance(point, tuple) or len(point) != 2
                for point in self.points
            )
        ):
            raise ValueError(
                "PolygonProfileIR points must be at least three 2D tuples"
            )
        if self.segment_ids is not None:
            if (
                not isinstance(self.segment_ids, tuple)
                or len(self.segment_ids) != len(self.points)
                or any(
                    not isinstance(value, str) or not value
                    for value in self.segment_ids
                )
                or len(set(self.segment_ids)) != len(self.segment_ids)
            ):
                raise ValueError(
                    "PolygonProfileIR segment_ids must uniquely name every edge"
                )


ProfileIR = CircleProfileIR | PolygonProfileIR


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


def _polygon_region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Return transport geometry for one qualified convex semantic polygon.

    Symbolic coordinates remain untouched in PolygonProfileIR. Current values
    are evaluated only to validate strict convexity and derive a backend
    selector when a native API requires one.
    """

    if (
        len(sketch.profiles) != 1
        or region.outer != 0
        or region.holes
        or not isinstance(sketch.profiles[0], PolygonProfileIR)
    ):
        raise ValueError(
            "qualified polygon region requires one outer PolygonProfileIR"
        )

    profile = sketch.profiles[0]
    points = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in points for value in point):
        raise ValueError("qualified polygon region coordinates must be finite")
    if len(set(points)) != len(points):
        raise ValueError("qualified polygon region has duplicate vertices")

    crosses = []
    count = len(points)
    for index in range(count):
        a = points[index]
        b = points[(index + 1) % count]
        c = points[(index + 2) % count]
        ab = (b[0] - a[0], b[1] - a[1])
        bc = (c[0] - b[0], c[1] - b[1])
        if hypot(*ab) <= 1e-12:
            raise ValueError("qualified polygon region has a zero-length edge")
        cross = ab[0] * bc[1] - ab[1] * bc[0]
        if abs(cross) <= 1e-12:
            raise ValueError(
                "qualified polygon region currently requires strict convexity"
            )
        crosses.append(cross)

    if not (
        all(value > 0 for value in crosses)
        or all(value < 0 for value in crosses)
    ):
        raise ValueError(
            "qualified polygon region currently requires a convex polygon"
        )

    # The arithmetic vertex centroid is strictly inside a convex polygon.
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
    )


def _region_interior_point(
    sketch: SketchIR,
    region: RegionIR,
) -> tuple[float, float]:
    """Derive backend transport from semantic profile/region geometry."""

    if (
        0 <= region.outer < len(sketch.profiles)
        and isinstance(sketch.profiles[region.outer], PolygonProfileIR)
    ):
        return _polygon_region_interior_point(sketch, region)
    return _circle_region_interior_point(sketch, region)


@dataclass(frozen=True)
class ExtrudeIR:
    """Distance extrusion over semantic Sketch regions."""

    sketch: SketchIR
    regions: tuple[RegionIR, ...]
    distance: Any
    direction: str
    source_kind: str = "sketch_base_extrusion"


@dataclass(frozen=True)
class RevolveIR:
    """Angular sweep of one semantic Sketch region around a principal axis."""

    sketch: SketchIR
    region: RegionIR
    axis: str
    angle: Any
    direction: str | None = None
    source_kind: str = "sketch_base_revolve"

    def __post_init__(self):
        if self.axis not in {"X", "Y", "Z"}:
            raise ValueError("RevolveIR axis must be X, Y or Z")
        if self.direction not in (None, "symmetric"):
            raise ValueError("RevolveIR direction must be None or symmetric")


@dataclass(frozen=True)
class FaceBoundaryIR:
    """Semantic request for all boundary edges of cardinal planar faces."""

    faces: tuple[str, ...]


@dataclass(frozen=True)
class ChamferIR:
    """Equal-distance chamfer over one qualified typed body result."""

    base: "PlacementIR | ExtrudeIR"
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
    | RevolveIR
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


def _angle_parameter_names(value, found=None):
    """Collect parameters whose qualified semantic role is an angle."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "sketch_base_revolve":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                angle,
                _axis,
                _direction,
                _operations,
                _rotation,
            ) = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
        _angle_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _angle_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _angle_parameter_names(item, found)
    return found


def _parameter_ir(shape: Shape) -> tuple[ParameterIR, ...]:
    angle_parameters = _angle_parameter_names(shape)
    return tuple(
        ParameterIR(
            name,
            value,
            unit="deg" if name in angle_parameters else "mm",
        )
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
    """Normalize the qualified standalone Sketch + Extrude slices."""
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
    if direction not in ("positive", "negative", "symmetric"):
        return None

    # Bounded straight-segment feature-composition slice (#351).
    if len(profiles) == 1 and profiles[0][0].kind == "polygon":
        if direction != "symmetric":
            return None
        if profile_picks is not None or exact_regions:
            return None

        profile, profile_anchor, offset = profiles[0]
        if profile_anchor is not None or tuple(offset) != (0, 0):
            return None
        points, profile_plane, ids = profile.data
        if profile_plane != plane or any(
            parameters_in(value)
            for point in points
            for value in point
        ):
            return None

        polygon = PolygonProfileIR(
            points=tuple(tuple(point) for point in points),
            segment_ids=tuple(ids) if ids is not None else None,
        )
        sketch = SketchIR(
            name=sketch_name,
            plane=plane,
            profiles=(polygon,),
        )
        region = RegionIR(outer=0)
        try:
            _polygon_region_interior_point(sketch, region)
        except ValueError:
            return None
        return ExtrudeIR(
            sketch=sketch,
            regions=(region,),
            distance=distance,
            direction=direction,
        )

    # Circle and annular slices qualified by #282/#320.
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


def _portable_revolve(shape: Shape) -> RevolveIR | None:
    """Normalize the first qualified standalone Sketch + Revolve slice."""
    if shape.kind != "sketch_base_revolve":
        return None

    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        angle,
        axis,
        direction,
        operations,
        rotation,
    ) = shape.data

    if plane != "XZ":
        return None
    if origin is not None or plane_offset is not None or rotation is not None:
        return None
    if operations or direction is not None or axis != "X":
        return None
    if len(profiles) != 1:
        return None

    profile, profile_anchor, offset = profiles[0]
    if (
        profile.kind != "polygon"
        or profile_anchor is not None
        or tuple(offset) != (0, 0)
    ):
        return None

    points, profile_plane, ids = profile.data
    if profile_plane != plane:
        return None

    sweep = pv(angle)
    if not isfinite(sweep) or sweep <= 0 or sweep > 360:
        return None

    angle_parameters = {
        parameter.name for parameter in parameters_in(angle)
    }
    coordinate_parameters = {
        parameter.name
        for point in points
        for value in point
        for parameter in parameters_in(value)
    }
    if angle_parameters & coordinate_parameters:
        return None

    polygon = PolygonProfileIR(
        points=tuple(tuple(point) for point in points),
        segment_ids=tuple(ids) if ids is not None else None,
    )
    sketch = SketchIR(
        name=sketch_name,
        plane=plane,
        profiles=(polygon,),
    )
    region = RegionIR(outer=0)
    try:
        _polygon_region_interior_point(sketch, region)
    except ValueError:
        return None

    return RevolveIR(
        sketch=sketch,
        region=region,
        axis=axis,
        angle=angle,
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
    # That surface is not yet a qualified portable IR capability.
    if distance2 is not None or flip:
        return None
    if not isinstance(edges, _FaceBoundarySelection) or not edges.faces:
        return None

    semantic_faces = tuple(Faces(face).value for face in edges.faces)

    placement = _portable_placement(base)
    if placement is not None:
        if (
            not isinstance(placement.primitive, BoxIR)
            or len(semantic_faces) != 1
        ):
            return None
        base_ir: PlacementIR | ExtrudeIR = placement
    else:
        extrude = _portable_extrude(base)
        if (
            extrude is None
            or extrude.direction != "symmetric"
            or extrude.sketch.plane != "XZ"
            or len(extrude.sketch.profiles) != 1
            or not isinstance(extrude.sketch.profiles[0], PolygonProfileIR)
            or semantic_faces != ("front", "back")
        ):
            return None
        base_ir = extrude

    return ChamferIR(
        base=base_ir,
        distance=distance,
        edges=FaceBoundaryIR(semantic_faces),
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

    revolve = _portable_revolve(shape)
    if revolve is not None:
        return revolve

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
    "PolygonProfileIR",
    "PrimitiveIR",
    "ProfileIR",
    "RegionIR",
    "RevolveIR",
    "SketchIR",
    "SphereIR",
    "_polygon_region_interior_point",
    "_region_interior_point",
    "is_portable",
    "normalize_shape",
]
