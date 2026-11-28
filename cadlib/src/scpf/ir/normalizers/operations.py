"""Revolve, topology selector and modifier normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from math import isfinite

from ...core import (
    Anchor,
    Edges,
    Expression,
    Faces,
    Parameter,
    Shape,
    _DirectionSelector,
    _FaceBoundarySelection,
    _ProfileEdgeSelection,
    _pv as pv,
)
from ..base import BodyIR, PlacementIR
from ..operations import (
    AxisLineIR,
    ChamferIR,
    DirectionPairEdgeSetIR,
    EdgeSelectionIR,
    ExplicitEdgePicksIR,
    FaceBoundaryIR,
    FilletIR,
    ParallelEdgeSetIR,
    ProfileEdgeSetIR,
    RevolveIR,
)
from ..profiles import (
    CircleProfileIR,
    PolygonProfileIR,
    RectangleProfileIR,
    RegionIR,
    RoundedRectangleProfileIR,
)
from ..sketch import PlaneIR, SketchChainIR
from .profiles import _region_interior_point
from .body import _normalize_node
from .sketch import _PLANE_AXES, _PLANE_NORMAL_INDEX, _same_semantic_dimension, _sketch_ir_from_payload

def _axis_line_ir(axis) -> AxisLineIR | None:
    """Normalize public principal/custom axis intent without native ids."""
    if isinstance(axis, str):
        if axis not in {"X", "Y", "Z"}:
            return None
        return AxisLineIR(direction=axis)

    if (
        not isinstance(axis, (tuple, list))
        or len(axis) != 2
    ):
        return None
    origin, direction = axis
    if (
        not isinstance(origin, (tuple, list))
        or len(origin) != 3
        or not isinstance(direction, (tuple, list))
        or len(direction) != 3
    ):
        return None

    vector = tuple(float(value) for value in direction)
    principal = {
        "X": (1.0, 0.0, 0.0),
        "Y": (0.0, 1.0, 0.0),
        "Z": (0.0, 0.0, 1.0),
    }
    semantic_direction = next(
        (
            name
            for name, expected in principal.items()
            if all(
                abs(actual - wanted) <= 1e-12
                for actual, wanted in zip(vector, expected)
            )
        ),
        None,
    )
    if semantic_direction is None:
        return None

    try:
        return AxisLineIR(
            direction=semantic_direction,
            origin=tuple(origin),
        )
    except ValueError:
        return None


def _axis_line_in_sketch_plane(axis: AxisLineIR, plane: PlaneIR) -> bool:
    """Check semantic coplanarity for the bounded principal-plane slice."""
    if (
        not isinstance(plane, PlaneIR)
        or axis.direction not in _PLANE_AXES[plane.orientation]
    ):
        return False
    normal_index = _PLANE_NORMAL_INDEX[plane.orientation]
    return _same_semantic_dimension(
        axis.origin[normal_index],
        plane.origin[normal_index],
    )


def _contains_untyped_expression(value) -> bool:
    """Return whether authored intent contains compatibility-only expression text."""
    if isinstance(value, Expression):
        return value.scalar_ir is None
    if isinstance(value, Shape):
        return _contains_untyped_expression(value.data)
    if isinstance(value, dict):
        return any(
            _contains_untyped_expression(key)
            or _contains_untyped_expression(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_untyped_expression(item) for item in value)
    return False


def _portable_revolve(
    shape: Shape,
    *,
    operation: str = "new_body",
    target: PlacementIR | None = None,
) -> RevolveIR | None:
    """Normalize the complete current public standalone Sketch Revolve grammar."""
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

    if origin is not None or rotation is not None or len(profiles) != 1:
        return None
    if operations:
        return None
    if _contains_untyped_expression(
        (profiles, angle, axis, plane_offset)
    ):
        return None
    if direction not in (None, "symmetric"):
        return None
    if operation not in {"new_body", "cut"}:
        return None
    if operation == "new_body" and target is not None:
        return None
    if operation == "cut" and not isinstance(target, PlacementIR):
        return None

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        operations,
        rotation,
    )
    if (
        sketch is None
        or sketch.support is not None
        or sketch.graph is None
        or len(sketch.graph.entities) != 1
        or sketch.graph.operations
        or not isinstance(
            sketch.graph.entities[0],
            (
                CircleProfileIR,
                RectangleProfileIR,
                RoundedRectangleProfileIR,
                PolygonProfileIR,
                SketchChainIR,
            ),
        )
    ):
        return None

    axis_ir = _axis_line_ir(axis)
    if axis_ir is None or not _axis_line_in_sketch_plane(
        axis_ir,
        sketch.plane,
    ):
        return None

    # A direct supported closed profile retains one explicit semantic region.
    # A connected profile is a completed Sketch-chain result; public Revolve
    # consumes that result as a whole and has no profile-selector argument.
    region = None
    if (
        sketch.graph is not None
        and not sketch.graph.operations
        and len(sketch.profiles) == 1
        and len(sketch.graph.entities) == 1
    ):
        candidate = RegionIR(outer=0)
        try:
            _region_interior_point(sketch, candidate)
        except ValueError:
            pass
        else:
            region = candidate

    try:
        return RevolveIR(
            sketch=sketch,
            region=region,
            axis=axis_ir,
            angle=angle,
            direction=direction,
            operation=operation,
            target=target,
        )
    except ValueError:
        return None



def _edge_selection_ir(edges) -> EdgeSelectionIR | None:
    """Normalize the public shared fillet/chamfer selector vocabulary."""
    if edges is Edges.VERTICAL:
        return ParallelEdgeSetIR("Z")

    if isinstance(edges, _FaceBoundarySelection):
        try:
            return FaceBoundaryIR(
                tuple(Faces(face).value for face in edges.faces)
            )
        except (TypeError, ValueError):
            return None

    if isinstance(edges, _ProfileEdgeSelection):
        try:
            return ProfileEdgeSetIR(
                patterns=tuple(edges.patterns),
                kind=edges.kind,
                sides=edges.sides,
            )
        except (TypeError, ValueError):
            return None

    if (
        isinstance(edges, (tuple, list))
        and edges
        and all(isinstance(edge, (Anchor, _DirectionSelector)) for edge in edges)
    ):
        vectors = []
        for edge in edges:
            try:
                vector = (
                    tuple(int(value) for value in edge.vector)
                    if isinstance(edge, Anchor)
                    else tuple(edge.vector)
                )
            except (TypeError, ValueError):
                return None
            vectors.append(vector)
        try:
            return DirectionPairEdgeSetIR(tuple(vectors))
        except ValueError:
            return None

    if isinstance(edges, (tuple, list)) and edges:
        try:
            return ExplicitEdgePicksIR(
                tuple(tuple(point) for point in edges)
            )
        except (TypeError, ValueError):
            return None

    return None


def _portable_fillet(shape: Shape) -> FilletIR | None:
    """Normalize public constant-radius Fillet with shared selector semantics."""
    if shape.kind != "fillet" or len(shape.data) != 3:
        return None

    base_shape, radius, edges = shape.data
    semantic_edges = _edge_selection_ir(edges)
    if semantic_edges is None:
        return None
    if (
        isinstance(radius, bool)
        or not isinstance(radius, (int, float, Parameter, Expression))
        or not isfinite(pv(radius))
        or pv(radius) <= 0
    ):
        return None

    base = _normalize_node(base_shape)
    if not isinstance(base, BodyIR):
        return None

    try:
        return FilletIR(base=base, radius=radius, edges=semantic_edges)
    except ValueError:
        return None


def _portable_chamfer(shape: Shape) -> ChamferIR | None:
    """Normalize public Chamfer with the shared semantic edge vocabulary."""
    if shape.kind != "chamfer":
        return None

    if len(shape.data) == 3:
        base_shape, distance, edges = shape.data
        distance2 = None
        flip = False
    elif len(shape.data) == 5:
        base_shape, distance, edges, distance2, flip = shape.data
    else:
        return None

    if not isinstance(flip, bool) or (flip and distance2 is None):
        return None
    semantic_edges = _edge_selection_ir(edges)
    if semantic_edges is None:
        return None

    base = _normalize_node(base_shape)
    if not isinstance(base, BodyIR):
        return None

    try:
        return ChamferIR(
            base=base,
            distance=distance,
            edges=semantic_edges,
            distance2=distance2,
            flip=flip,
        )
    except ValueError:
        return None
