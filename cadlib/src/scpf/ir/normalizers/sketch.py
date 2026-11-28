"""Sketch, profile, region and extrude normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from math import isfinite

from ...core import Anchor, Depth, Shape, _dim_add, _pv as pv, parameters_in
from ..base import BodyIR
from ..body import IRNode
from ..operations import ExtrudeIR
from ..sketch import (
    CircleProfileIR,
    PlaneIR,
    PolygonProfileIR,
    ProfileIR,
    RectangleProfileIR,
    RegionIR,
    RoundedRectangleProfileIR,
    SketchChainIR,
    SketchChainSegmentIR,
    SketchCoordinateDimensionIR,
    SketchEntityGraphIR,
    SketchEntityRefIR,
    SketchGraphEntityIR,
    SketchIR,
    SketchLengthDimensionIR,
    SketchLineIR,
    SketchMirrorIR,
    SketchOrientationConstraintIR,
    SketchPointIR,
    SketchRectangularPatternIR,
    SketchRelationsIR,
    SketchSupportIR,
    SlotProfileIR,
    TextEntityIR,
    _circle_profile_radii,
    _concentric_circle_region_from_pick,
    _region_interior_point,
)

def _plane_ir(orientation: str, offset=None) -> PlaneIR | None:
    """Normalize one principal standalone Sketch plane without native ids."""
    if orientation not in _PLANE_NORMAL_INDEX:
        return None
    distance = 0 if offset is None else offset
    origin = [0, 0, 0]
    origin[_PLANE_NORMAL_INDEX[orientation]] = distance
    try:
        return PlaneIR(orientation=orientation, origin=tuple(origin))
    except ValueError:
        return None


def _semantic_dimension_key(value):
    """Identity key for authored CAD dimensions without evaluating symbols."""
    parameters = parameters_in(value)
    if not parameters:
        return ("number", float(pv(value)))
    expression = getattr(value, "expression", None)
    if not isinstance(expression, str) or not expression:
        return None
    return (
        "expression",
        expression,
        tuple(parameter.name for parameter in parameters),
    )


def _same_semantic_dimension(left, right) -> bool:
    """Compare authored dimension intent, using values only when non-symbolic."""
    if left is right:
        return True
    left_key = _semantic_dimension_key(left)
    right_key = _semantic_dimension_key(right)
    if left_key is None or right_key is None:
        return False
    if left_key[0] == right_key[0] == "number":
        return abs(left_key[1] - right_key[1]) <= 1e-12
    return left_key == right_key


def _parameterized_rectangle_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize the bounded #440 rectangle relation graph before lowering."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or len(profile.points) != 4
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    p1, p2, p3, p4 = profile.points
    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    # This first slice is deliberately the already-qualified origin-based
    # axis-aligned rectangle from native-revolve. Compare symbolic equality
    # without baking current values into semantic identity.
    if any(parameters_in(value) for value in (p1[0], p1[1], p2[0], p4[1])):
        return None
    if (
        abs(values[0][0]) > 1e-12
        or abs(values[0][1]) > 1e-12
        or abs(values[1][0]) > 1e-12
        or abs(values[3][1]) > 1e-12
        or not _same_semantic_dimension(p2[1], p3[1])
        or not _same_semantic_dimension(p3[0], p4[0])
        or values[1][1] <= 0
        or values[2][0] <= 0
    ):
        return None

    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=(
            SketchLineIR(0, 1),
            SketchLineIR(1, 2),
            SketchLineIR(2, 3),
            SketchLineIR(3, 0),
        ),
        constraints=(
            SketchOrientationConstraintIR(0, "vertical"),
            SketchOrientationConstraintIR(1, "horizontal"),
            SketchOrientationConstraintIR(2, "vertical"),
            SketchOrientationConstraintIR(3, "horizontal"),
        ),
        dimensions=(
            SketchLengthDimensionIR(0, p2[1]),
            SketchLengthDimensionIR(1, p3[0]),
        ),
    )


def _parameterized_polygon_coordinate_relations(
    profile: PolygonProfileIR,
) -> SketchRelationsIR | None:
    """Normalize generic parameterized Polygon point coordinates into Sketch IR."""
    if (
        not isinstance(profile, PolygonProfileIR)
        or not any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
    ):
        return None

    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(not isfinite(value) for point in values for value in point):
        return None

    point_count = len(profile.points)
    return SketchRelationsIR(
        points=tuple(
            SketchPointIR(position=tuple(point))
            for point in profile.points
        ),
        lines=tuple(
            SketchLineIR(index, (index + 1) % point_count)
            for index in range(point_count)
        ),
        coordinate_dimensions=tuple(
            SketchCoordinateDimensionIR(
                point=index,
                axis=axis,
                value=point[coordinate],
            )
            for index, point in enumerate(profile.points)
            for coordinate, axis in enumerate(("x", "y"))
        ),
    )


def _profile_ir_from_shape(
    profile: Shape,
    profile_anchor,
    offset,
    plane: str,
) -> ProfileIR | None:
    try:
        offset = tuple(offset)
        if len(offset) != 2:
            return None

        if profile.kind == "circle":
            if profile_anchor is not Anchor.CENTER:
                return None
            (diameter,) = profile.data
            return CircleProfileIR(
                diameter=diameter,
                center=offset,
            )

        if profile.kind == "rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth = profile.data
            return RectangleProfileIR(
                width=width,
                depth=depth,
                center=offset,
            )

        if profile.kind == "rounded_rectangle":
            if profile_anchor is not Anchor.CENTER:
                return None
            width, depth, radius = profile.data
            return RoundedRectangleProfileIR(
                width=width,
                depth=depth,
                radius=radius,
                center=offset,
            )

        if profile.kind == "polygon":
            if profile_anchor is not None:
                return None
            points, profile_plane, ids = profile.data
            if profile_plane != plane:
                return None
            shifted = tuple(
                tuple(
                    _dim_add(value, offset[index])
                    for index, value in enumerate(point)
                )
                for point in points
            )
            return PolygonProfileIR(
                points=shifted,
                segment_ids=tuple(ids) if ids is not None else None,
            )

        if profile_anchor is not None:
            return None

        if profile.kind == "slot_center_to_center":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="center_to_center",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_overall":
            p0, p1, width = profile.data
            return SlotProfileIR(
                construction="overall",
                points=(tuple(p0), tuple(p1)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_center_point":
            center, end, width = profile.data
            return SlotProfileIR(
                construction="center_point",
                points=(tuple(center), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_three_point":
            start, through, end, width = profile.data
            return SlotProfileIR(
                construction="arc_three_point",
                points=(tuple(start), tuple(through), tuple(end)),
                width=width,
                offset=offset,
            )
        if profile.kind == "slot_arc_center":
            center, start, end, sweep, width = profile.data
            if end is not None:
                return SlotProfileIR(
                    construction="arc_center_end",
                    points=(tuple(center), tuple(start), tuple(end)),
                    width=width,
                    offset=offset,
                )
            return SlotProfileIR(
                construction="arc_center_sweep",
                points=(tuple(center), tuple(start)),
                width=width,
                sweep=float(sweep),
                offset=offset,
            )
    except (TypeError, ValueError):
        return None

    return None


def _sketch_graph_from_payload(
    sketch_name,
    plane,
    profiles,
    operations,
) -> SketchEntityGraphIR | None:
    """Normalize stored Sketch entities/operations without requiring Sketch object state."""
    class _PayloadSketch:
        pass

    sketch = _PayloadSketch()
    sketch.name = sketch_name
    sketch.plane = plane

    entities = []
    references = {}
    for index, (profile, profile_anchor, offset) in enumerate(profiles):
        semantic = _sketch_graph_profile_ir(
            sketch,
            profile,
            profile_anchor,
            offset,
        )
        if semantic is None:
            return None
        entities.append(semantic)
        references[id(profile)] = SketchEntityRefIR("entity", index)

    semantic_operations = []
    for index, operation in enumerate(operations):
        source = operation.data[0]
        source_ref = references.get(id(source))
        if source_ref is None:
            return None
        try:
            if operation.kind == "sketch_pattern_rectangular":
                (
                    _source,
                    count,
                    spacing,
                    direction,
                    count2,
                    spacing2,
                    direction2,
                    alignment,
                    alignment2,
                    reversed1,
                    reversed2,
                ) = operation.data
                semantic = SketchRectangularPatternIR(
                    source=source_ref,
                    count=count,
                    spacing=spacing,
                    direction=tuple(direction),
                    count2=count2,
                    spacing2=spacing2,
                    direction2=(
                        tuple(direction2)
                        if direction2 is not None
                        else None
                    ),
                    alignment=alignment,
                    alignment2=alignment2,
                    reversed=reversed1,
                    reversed2=reversed2,
                )
            elif operation.kind == "sketch_mirror":
                _source, axis = operation.data
                semantic = SketchMirrorIR(
                    source=source_ref,
                    axis=axis,
                )
            else:
                return None
        except (TypeError, ValueError):
            return None
        semantic_operations.append(semantic)
        references[id(operation)] = SketchEntityRefIR(
            "operation",
            index,
        )

    try:
        return SketchEntityGraphIR(
            entities=tuple(entities),
            operations=tuple(semantic_operations),
        )
    except ValueError:
        return None


def _sketch_ir_from_payload(
    sketch_name,
    plane,
    origin,
    plane_offset,
    profiles,
    operations,
    rotation,
    *,
    support: SketchSupportIR | None = None,
) -> SketchIR | None:
    if plane not in ("XY", "XZ", "YZ"):
        return None
    if origin is not None and plane_offset is not None:
        return None
    if origin is not None:
        try:
            plane_ir = PlaneIR(
                orientation=plane,
                origin=tuple(origin),
            )
        except (TypeError, ValueError):
            return None
    else:
        plane_ir = _plane_ir(plane, plane_offset)
    if plane_ir is None:
        return None

    graph = _sketch_graph_from_payload(
        sketch_name,
        plane,
        profiles,
        operations,
    )
    if graph is None:
        return None

    semantic_profiles = tuple(
        entity
        for entity in graph.entities
        if isinstance(
            entity,
            (
                CircleProfileIR,
                RectangleProfileIR,
                RoundedRectangleProfileIR,
                SlotProfileIR,
                PolygonProfileIR,
            ),
        )
    )
    relations = None
    if (
        len(semantic_profiles) == 1
        and isinstance(semantic_profiles[0], PolygonProfileIR)
    ):
        polygon = semantic_profiles[0]
        relations = (
            _parameterized_rectangle_relations(polygon)
            or _parameterized_polygon_coordinate_relations(polygon)
        )

    try:
        return SketchIR(
            name=sketch_name,
            plane=plane_ir,
            profiles=semantic_profiles,
            relations=relations,
            support=support,
            rotation=(
                None
                if rotation is None
                else tuple(float(value) for value in rotation)
            ),
            graph=graph,
        )
    except (TypeError, ValueError):
        return None


def _extrude_regions(
    sketch: SketchIR,
    profile_picks,
    exact_regions,
) -> tuple[RegionIR, ...] | None:
    """Normalize public all-region or point-selected region intent.

    Existing directly-resolvable concentric/polygon families retain stronger
    semantic boundary membership. General picks remain authored selector intent.
    """
    if profile_picks is not None:
        if not isinstance(profile_picks, (tuple, list)):
            return None

        # A single explicitly selected profile remains explicit selector intent
        # so the native command preserves its authored profiles=[...] spelling.
        if len(sketch.profiles) == 1:
            try:
                return tuple(
                    RegionIR(
                        selector=tuple(float(value) for value in point),
                        exact=exact_regions,
                    )
                    for point in profile_picks
                )
            except (TypeError, ValueError):
                return None

        # Preserve the already-qualified stronger membership model only when
        # the source really is the bounded concentric-circle family.
        concentric = (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and sketch.profiles
            and all(
                isinstance(profile, CircleProfileIR)
                for profile in sketch.profiles
            )
            and len(sketch.profiles) == len(sketch.graph.entities)
        )
        if concentric:
            try:
                _circle_profile_radii(sketch)
            except ValueError:
                concentric = False

        if concentric:
            try:
                return tuple(
                    _concentric_circle_region_from_pick(sketch, point)
                    for point in profile_picks
                )
            except ValueError:
                return None

        # Preserve exact single-polygon membership for the older qualified
        # profile contract (normally reached above only if graph/profile
        # composition changes later).
        if (
            exact_regions
            and sketch.graph is not None
            and not sketch.graph.operations
            and len(sketch.profiles) == 1
            and isinstance(sketch.profiles[0], PolygonProfileIR)
            and len(profile_picks) == 1
        ):
            try:
                return (
                    _polygon_region_from_exact_pick(
                        sketch,
                        profile_picks[0],
                    ),
                )
            except ValueError:
                return None

        try:
            return tuple(
                RegionIR(
                    selector=tuple(float(value) for value in point),
                    exact=exact_regions,
                )
                for point in profile_picks
            )
        except (TypeError, ValueError):
            return None

    if exact_regions:
        return None

    if (
        sketch.graph is not None
        and not sketch.graph.operations
        and len(sketch.profiles) == 1
        and len(sketch.graph.entities) == 1
        and not isinstance(sketch.graph.entities[0], TextEntityIR)
    ):
        try:
            region = RegionIR(outer=0)
            _region_interior_point(sketch, region)
            return (region,)
        except ValueError:
            pass
    return ()


def _portable_extrude(shape: Shape) -> ExtrudeIR | None:
    """Normalize standalone Sketch + Extrude semantics."""
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

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        operations,
        rotation,
    )
    if sketch is None or direction not in {
        "positive", "negative", "symmetric"
    }:
        return None
    regions = _extrude_regions(
        sketch,
        profile_picks,
        exact_regions,
    )
    if regions is None:
        return None
    if distance is Depth.THROUGH_ALL:
        return None

    try:
        return ExtrudeIR(
            sketch=sketch,
            regions=regions,
            distance=distance,
            direction=direction,
        )
    except ValueError:
        return None


def _portable_attached_extrude(
    target: IRNode,
    target_shape: Shape,
    tool_shape: Shape,
    operation: str,
) -> ExtrudeIR | None:
    """Normalize Sketch(on=...) extrusion over one already-typed target."""
    if (
        not isinstance(target, BodyIR)
        or tool_shape.kind != "explicit_sketch_extrusion"
        or operation not in {"join", "cut"}
    ):
        return None

    (
        sketch_name,
        authored_target,
        parent_anchor,
        plane_info,
        profiles,
        distance,
        direction,
        operations,
        profile_picks,
        exact_regions,
    ) = tool_shape.data
    if authored_target is not target_shape:
        return None
    plane_name, sketch_origin, sketch_rotation = plane_info

    # A default supported Sketch uses the public anchor surface. An explicit
    # plane remains a world frame while target still owns the body operation.
    if plane_name is None:
        try:
            parent = Anchor(parent_anchor).value
        except (TypeError, ValueError):
            return None
        plane_name = "XY"
        support = SketchSupportIR(
            target=target,
            parent=parent,
        )
        semantic_origin = None
    else:
        support = SketchSupportIR(
            target=target,
            parent=None,
        )
        semantic_origin = sketch_origin

    sketch = _sketch_ir_from_payload(
        sketch_name,
        plane_name,
        semantic_origin,
        None,
        profiles,
        operations,
        sketch_rotation,
        support=support,
    )
    if sketch is None or direction not in {
        "positive", "negative", "symmetric"
    }:
        return None
    regions = _extrude_regions(
        sketch,
        profile_picks,
        exact_regions,
    )
    if regions is None:
        return None

    through_all = distance is Depth.THROUGH_ALL
    if through_all and operation != "cut":
        return None

    try:
        return ExtrudeIR(
            sketch=sketch,
            regions=regions,
            distance=None if through_all else distance,
            direction=direction,
            operation=operation,
            target=target,
            through_all=through_all,
            source_kind="explicit_sketch_extrusion",
        )
    except ValueError:
        return None

def _sketch_chain_ir(
    shape: Shape,
    *,
    closed: bool | None = None,
    name: str | None = None,
    plane: str | None = None,
    offset=(0, 0),
) -> SketchChainIR | None:
    """Normalize authored connected Sketch paths without native curve ids."""
    if shape.kind == "sketch_open_chain":
        sketch_name, orientation, plane_offset, _start, segments = shape.data
        if closed is True:
            return None
        plane_ir = _plane_ir(orientation, plane_offset)
        if plane_ir is None:
            return None
        chain_name = sketch_name
        is_closed = False
        profile_offset = (0, 0)
    elif shape.kind == "connected_profile":
        if closed is False or name is None:
            return None
        _start, segments = shape.data
        plane_ir = _plane_ir(plane) if plane is not None else None
        if plane is not None and plane_ir is None:
            return None
        chain_name = name
        is_closed = True
        profile_offset = tuple(offset)
        if len(profile_offset) != 2:
            return None
    else:
        return None

    semantic = []
    for segment in segments:
        kind = segment[0]
        if kind == "line":
            _kind, start, end = segment
            through = center = None
            clockwise = None
        elif kind == "arc_tangent":
            _kind, start, end = segment
            through = center = None
            clockwise = None
        elif kind == "arc_three_point":
            _kind, start, end, through = segment
            center = None
            clockwise = None
        elif kind == "arc_center_point":
            _kind, start, end, center, clockwise = segment
            through = None
        else:
            return None

        def shifted(point):
            if point is None:
                return None
            return tuple(
                _dim_add(point[index], profile_offset[index])
                for index in range(2)
            )

        try:
            semantic.append(
                SketchChainSegmentIR(
                    kind=kind,
                    start=shifted(start),
                    end=shifted(end),
                    through=shifted(through),
                    center=shifted(center),
                    clockwise=clockwise,
                )
            )
        except ValueError:
            return None

    try:
        return SketchChainIR(
            name=chain_name,
            plane=plane_ir,
            segments=tuple(semantic),
            closed=is_closed,
        )
    except ValueError:
        return None


def _sketch_graph_profile_ir(
    sketch,
    profile: Shape,
    profile_anchor,
    offset,
) -> SketchGraphEntityIR | None:
    if profile.kind == "text":
        if profile_anchor is not None:
            return None
        text, height, font = profile.data
        try:
            return TextEntityIR(
                text=text,
                height=height,
                font=font,
                position=tuple(offset),
            )
        except (TypeError, ValueError):
            return None

    if profile.kind == "connected_profile":
        if profile_anchor is not None:
            return None
        return _sketch_chain_ir(
            profile,
            closed=True,
            name=sketch.name,
            plane=sketch.plane,
            offset=offset,
        )

    semantic_plane = sketch.plane
    if semantic_plane is None and profile.kind == "polygon":
        semantic_plane = profile.data[1]
    if semantic_plane is None:
        semantic_plane = "XY"
    return _profile_ir_from_shape(
        profile,
        profile_anchor,
        offset,
        semantic_plane,
    )


def normalize_sketch_entities(sketch) -> SketchEntityGraphIR:
    """Normalize public Sketch contents independently from support/consumers."""
    from ...explicit_sketch import Sketch

    if not isinstance(sketch, Sketch):
        raise TypeError("Sketch entity normalization requires a Sketch")
    if not sketch._closed or sketch._token is not None:
        raise ValueError(
            "Sketch entity normalization requires a completed Sketch scope"
        )

    entities = []
    references = {}
    for index, (profile, profile_anchor, offset) in enumerate(
        sketch._profiles
    ):
        semantic = _sketch_graph_profile_ir(
            sketch,
            profile,
            profile_anchor,
            offset,
        )
        if semantic is None:
            raise ValueError(
                f"Sketch entity {profile.kind!r} is outside semantic graph IR"
            )
        entities.append(semantic)
        references[id(profile)] = SketchEntityRefIR("entity", index)

    open_chains = []
    for chain in sketch._chains:
        semantic = _sketch_chain_ir(chain, closed=False)
        if semantic is None:
            raise ValueError(
                "Sketch open chain is outside semantic SketchChainIR"
            )
        open_chains.append(semantic)

    operations = []
    for index, operation in enumerate(sketch._operations):
        source = operation.data[0]
        source_ref = references.get(id(source))
        if source_ref is None:
            raise ValueError(
                "Sketch operation source has no semantic graph identity"
            )

        if operation.kind == "sketch_pattern_rectangular":
            (
                _source,
                count,
                spacing,
                direction,
                count2,
                spacing2,
                direction2,
                alignment,
                alignment2,
                reversed1,
                reversed2,
            ) = operation.data
            semantic = SketchRectangularPatternIR(
                source=source_ref,
                count=count,
                spacing=spacing,
                direction=tuple(direction),
                count2=count2,
                spacing2=spacing2,
                direction2=(
                    tuple(direction2)
                    if direction2 is not None
                    else None
                ),
                alignment=alignment,
                alignment2=alignment2,
                reversed=reversed1,
                reversed2=reversed2,
            )
        elif operation.kind == "sketch_mirror":
            _source, axis = operation.data
            semantic = SketchMirrorIR(
                source=source_ref,
                axis=axis,
            )
        else:
            raise ValueError(
                f"unsupported Sketch operation {operation.kind!r}"
            )

        operations.append(semantic)
        references[id(operation)] = SketchEntityRefIR(
            "operation",
            index,
        )

    return SketchEntityGraphIR(
        entities=tuple(entities),
        open_chains=tuple(open_chains),
        operations=tuple(operations),
    )
