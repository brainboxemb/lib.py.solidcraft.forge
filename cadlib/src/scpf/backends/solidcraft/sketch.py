"""SolidCraft lowering for sketches, profiles and reference geometry."""
from __future__ import annotations

from fnmatch import fnmatchcase
from math import isfinite

from ...compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from ...core import (
    Expression,
    Parameter,
    _DirectionSelector,
    _dim_abs,
    _dim_add,
    _dim_sub,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _cylinder_base_from_anchor,
    _primitive_center_from_anchor,
    _sphere_center_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    command_value,
    half,
    midpoint,
    number_text,
    parameters_in,
)
from ...ir import (
    AxisLineIR,
    BodyIR,
    BossFeatureIR,
    BoundOffsetIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CircularPatternIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    DirectionPairEdgeSetIR,
    ExplicitEdgePicksIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FeaturePlacementIR,
    FeatureRefIR,
    FilletIR,
    HoleIR,
    LipFeatureIR,
    LegacyShapeIR,
    ModelIR,
    NamedFeatureIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PlasticFeatureIR,
    PolygonProfileIR,
    ProfileEdgeSetIR,
    RegionIR,
    RectangleProfileIR,
    RectangularPatternIR,
    RevolveIR,
    RoundedRectangleProfileIR,
    SketchRelationsIR,
    SketchIR,
    SketchSupportIR,
    SketchChainIR,
    SketchEntityGraphIR,
    SketchEntityRefIR,
    SketchMirrorIR,
    SketchRectangularPatternIR,
    TextEntityIR,
    TranslationIR,
    SheetBaseIR,
    SheetContourFlangeIR,
    SheetEdgeFlangeIR,
    SheetFoldIR,
    SheetHemIR,
    SheetPathFlangeIR,
    SheetPerforateIR,
    SheetRuleIR,
    ShellIR,
    SlotProfileIR,
    SnapFitFeatureIR,
    SphereIR,
    RestFeatureIR,
    SuppressionColumnIR,
    _region_interior_point,
    resolve_feature_ref,
)
from ...placement import _combine
from ...replay import replay_document
from ...scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


from .common import _require_positive, _command, _role_command_value

_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}

_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}


def _next_face_query_index(commands: list[dict]) -> int:
    """Late bridge to face-query numbering without a sketch/operations cycle."""
    from .operations import _next_face_query_index as implementation
    return implementation(commands)


def _principal_plane_offset(plane: PlaneIR, *, label: str):
    """Return one bounded principal-plane offset without baking symbols."""
    if not isinstance(plane, PlaneIR):
        raise ModelError(f"{label} requires PlaneIR")
    normal = _PLANE_NORMAL_INDEX[plane.orientation]
    for index, value in enumerate(plane.origin):
        if index == normal:
            continue
        if parameters_in(value) or abs(pv(value)) > 1e-12:
            raise ModelError(
                f"{label} currently requires zero in-plane PlaneIR origin"
            )
    return plane.origin[normal]


def _solidcraft_sketch_create(sketch) -> dict:
    """Create one standalone/world-frame Sketch from semantic frame intent."""
    normal = _PLANE_NORMAL_INDEX[sketch.plane.orientation]
    rotation = getattr(sketch, "rotation", None)
    in_plane = tuple(
        value
        for index, value in enumerate(sketch.plane.origin)
        if index != normal
    )
    explicit_frame = (
        rotation is not None
        or any(parameters_in(value) or abs(pv(value)) > 1e-12 for value in in_plane)
    )
    if explicit_frame:
        from ..sketches import _sketch_plane_frame
        return _command(
            "sketch.create",
            plane=_sketch_plane_frame(
                sketch.plane.orientation,
                origin=sketch.plane.origin,
                rotation=rotation,
            ),
            name=sketch.name,
        )

    offset = _principal_plane_offset(
        sketch.plane,
        label="portable SolidCraft Sketch IR",
    )
    params = {
        "name": sketch.name,
        "plane": sketch.plane.orientation,
    }
    if parameters_in(offset) or abs(pv(offset)) > 1e-12:
        params["offset"] = command_value(offset)
    return _command("sketch.create", **params)


def _typed_rectangular_support(node: BodyIR):
    """Find the typed axis-aligned Box datum underlying one body history."""
    if isinstance(node, PlacementIR) and isinstance(node.primitive, BoxIR):
        return node, None
    if isinstance(node, HoleIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, PlasticFeatureIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, ShellIR):
        placement, _wall = _typed_rectangular_support(node.base)
        return placement, node.thickness
    if isinstance(node, (ChamferIR, FilletIR)):
        return _typed_rectangular_support(node.base)
    if isinstance(node, (RectangularPatternIR, CircularPatternIR)):
        return _typed_rectangular_support(node.base)
    if isinstance(node, BooleanIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, ExtrudeIR) and node.target is not None:
        return _typed_rectangular_support(node.target)
    raise ModelError(
        "BOTTOM/CENTER/INNER_BOTTOM Sketch support currently requires "
        "a typed rectangular Box history"
    )


def _solidcraft_sketch_support_commands(
    sketch: SketchIR,
    name: str,
    *,
    prior: list[dict],
) -> tuple[list[dict], tuple]:
    """Lower semantic Sketch support and return backend-local XY origin."""
    support = sketch.support
    if support is None or support.parent is None:
        return [_solidcraft_sketch_create(sketch)], (0, 0)
    if not isinstance(support, SketchSupportIR):
        raise ModelError("portable SolidCraft Sketch support is malformed")

    if support.parent == "top":
        index = _next_face_query_index(prior)
        point_var = f"$face_point_{index}"
        index_var = f"$face_index_{index}"
        selector = {
            "field": "faces",
            "where": {"plane_normal": [0, 0, 1]},
            "max": "area",
        }
        face_query = _command("model.faces", body=name)
        face_query["bind"] = {
            point_var: {**selector, "select": "point"},
            index_var: {**selector, "select": "index"},
        }
        return [
            face_query,
            _command(
                "sketch.create",
                plane={
                    "face": point_var,
                    "body": name,
                    "index": index_var,
                },
                project_edges=False,
                name=sketch.name,
            ),
        ], (0, 0)

    placement, wall = _typed_rectangular_support(support.target)
    primitive = placement.primitive
    corner = _box_corner_from_anchor(
        primitive.length,
        primitive.width,
        primitive.height,
        placement.point,
        _DirectionSelector(placement.anchor),
    )
    center_x = _combine(corner[0], half(primitive.length))
    center_y = _combine(corner[1], half(primitive.width))
    if support.parent == "bottom":
        plane_z = corner[2]
    elif support.parent == "center":
        plane_z = _combine(corner[2], half(primitive.height))
    elif support.parent == "inner_bottom":
        if wall is None:
            raise ModelError(
                "INNER_BOTTOM Sketch support requires typed ShellIR history"
            )
        plane_z = _combine(corner[2], wall)
    else:
        raise ModelError(
            f"unsupported portable Sketch support anchor {support.parent!r}"
        )

    params = {"plane": "XY", "name": sketch.name}
    if parameters_in(plane_z) or abs(pv(plane_z)) > 1e-12:
        params["offset"] = command_value(plane_z)
    return [_command("sketch.create", **params)], (center_x, center_y)


def _next_sketch_index(commands: list[dict]) -> int:
    return 1 + sum(
        command.get("command") == "sketch.create"
        for command in commands
    )


def _solidcraft_relation_polygon_points(sketch) -> tuple[tuple, ...] | None:
    """Coalesce explicit semantic relations into SolidCraft's symbolic polyline.

    SolidCraft can retain authored point expressions directly in sketch.line,
    so duplicate solver relations are unnecessary. The relation graph remains
    the semantic source; this lowering only chooses an efficient native spelling.
    """
    relations = sketch.relations
    if relations is None:
        return None
    if not isinstance(relations, SketchRelationsIR):
        raise ModelError("portable SolidCraft Sketch relations require SketchRelationsIR")

    count = len(relations.points)
    expected_lines = tuple(
        (index, (index + 1) % count)
        for index in range(count)
    )
    actual_lines = tuple(
        (line.start, line.end)
        for line in relations.lines
    )
    if actual_lines != expected_lines:
        raise ModelError(
            "portable SolidCraft Sketch relations require one closed line loop"
        )

    if relations.coordinate_dimensions:
        if relations.constraints or relations.dimensions:
            raise ModelError(
                "portable SolidCraft coordinate relations must not mix relation families"
            )
        expected = {
            (point, axis): command_value(relations.points[point].position[index])
            for point in range(count)
            for index, axis in enumerate(("x", "y"))
        }
        actual = {
            (dimension.point, dimension.axis): command_value(dimension.value)
            for dimension in relations.coordinate_dimensions
        }
        if actual != expected or len(relations.coordinate_dimensions) != 2 * count:
            raise ModelError(
                "portable SolidCraft coordinate relations must drive every point coordinate"
            )
        return tuple(point.position for point in relations.points)

    if count != 4:
        raise ModelError(
            "portable SolidCraft #440 relations require one four-line rectangle"
        )

    expected_orientations = (
        "vertical",
        "horizontal",
        "vertical",
        "horizontal",
    )
    actual_orientations = [None] * count
    for constraint in relations.constraints:
        if actual_orientations[constraint.line] is not None:
            raise ModelError(
                "portable SolidCraft #440 relations require one orientation per line"
            )
        actual_orientations[constraint.line] = constraint.orientation
    if tuple(actual_orientations) != expected_orientations:
        raise ModelError(
            "portable SolidCraft #440 relations require V/H/V/H rectangle constraints"
        )
    if tuple(dimension.line for dimension in relations.dimensions) != (0, 1):
        raise ModelError(
            "portable SolidCraft #440 relations require the two driving edge dimensions"
        )

    return tuple(point.position for point in relations.points)


def _solidcraft_dimension_sum(left, right):
    """Match the stable standalone Sketch symbolic coordinate spelling."""
    if isinstance(left, (int, float)) and left == 0:
        return right
    if isinstance(right, (int, float)) and right == 0:
        return left
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left + right
    native_left = command_value(left)
    native_right = command_value(right)
    return _native_expression(
        f"({native_left}) + ({native_right})",
        tuple(sorted(_native_dependencies((native_left, native_right)))),
    )


def _solidcraft_profile_commands(
    sketch: SketchIR,
    profile: ProfileIR,
    *,
    profile_index: int,
    origin_offset=(0, 0),
) -> list[dict]:
    """Lower one semantic closed profile without reading frontend Shape.data."""

    def shifted(point):
        return (
            _solidcraft_dimension_sum(origin_offset[0], point[0]),
            _solidcraft_dimension_sum(origin_offset[1], point[1]),
        )
    if isinstance(profile, CircleProfileIR):
        _require_positive(profile.diameter, "circle diameter")
        return [
            _command(
                "sketch.circle.center",
                center=[
                    command_value(value)
                    for value in shifted(profile.center)
                ],
                diameter=command_value(profile.diameter),
            )
        ]

    if isinstance(
        profile,
        (RectangleProfileIR, RoundedRectangleProfileIR),
    ):
        _require_positive(profile.width, "sketch rectangle width")
        _require_positive(profile.depth, "sketch rectangle height")
        center = shifted(profile.center)
        x0 = _solidcraft_dimension_sum(center[0], -half(profile.width))
        y0 = _solidcraft_dimension_sum(center[1], -half(profile.depth))
        x1 = _solidcraft_dimension_sum(center[0], half(profile.width))
        y1 = _solidcraft_dimension_sum(center[1], half(profile.depth))
        params = {
            "p0": [command_value(x0), command_value(y0)],
            "p1": [command_value(x1), command_value(y1)],
        }
        if isinstance(profile, RoundedRectangleProfileIR):
            _require_positive(profile.radius, "sketch rounded rectangle radius")
            if pv(profile.radius) * 2 >= min(
                pv(profile.width),
                pv(profile.depth),
            ):
                raise ModelError(
                    "rounded rectangle radius exceeds half the shorter side"
                )
            params["radius"] = command_value(profile.radius)
            command = "sketch.rectangle.rounded"
        else:
            command = "sketch.rectangle.two_point"
        return [_command(command, **params)]

    if isinstance(profile, PolygonProfileIR):
        relation_points = _solidcraft_relation_polygon_points(sketch)
        points = (
            relation_points
            if relation_points is not None
            else profile.points
        )
        ids = (
            list(profile.segment_ids)
            if profile.segment_ids is not None
            else [
                chr(ord("a") + index)
                for index in range(len(points))
            ]
        )
        return [
            _command(
                "sketch.line",
                points=[
                    [
                        command_value(value)
                        for value in shifted(point)
                    ]
                    for point in points
                ],
                closed=True,
                ids=ids,
            )
        ]

    if not isinstance(profile, SlotProfileIR):
        raise ModelError(
            f"unsupported portable SolidCraft profile {type(profile).__name__}"
        )

    _require_positive(profile.width, "slot width")
    commands = []

    def intent(point):
        return tuple(
            _combine(
                origin_offset[index],
                _combine(profile.offset[index], value),
            )
            for index, value in enumerate(point)
        )

    def direct_point(point):
        values = [command_value(value) for value in intent(point)]
        if any(isinstance(value, str) for value in values):
            raise ModelError(
                "native Slot point coordinates currently require fixed values"
            )
        return values

    def seed_point(point):
        return [pv(value) for value in point]

    def same_intent(left, right):
        return command_value(left) == command_value(right)

    def parametric_straight(
        command_name,
        key_a,
        point_a,
        key_b,
        point_b,
        *,
        center_point=False,
    ):
        intent_a = intent(point_a)
        intent_b = intent(point_b)
        dx = pv(intent_b[0]) - pv(intent_a[0])
        dy = pv(intent_b[1]) - pv(intent_a[1])
        tolerance = 1e-9
        if abs(dy) <= tolerance and abs(dx) > tolerance:
            axis = 0
            mode = "horizontal"
            if not same_intent(intent_a[1], intent_b[1]):
                raise ModelError(
                    "parametric horizontal Slot endpoints must share "
                    "the same y-coordinate intent"
                )
        elif abs(dx) <= tolerance and abs(dy) > tolerance:
            axis = 1
            mode = "vertical"
            if not same_intent(intent_a[0], intent_b[0]):
                raise ModelError(
                    "parametric vertical Slot endpoints must share "
                    "the same x-coordinate intent"
                )
        else:
            raise ModelError(
                "parametric straight Slot endpoints currently require "
                "a horizontal or vertical axis"
            )

        delta = _dim_abs(_dim_sub(intent_b[axis], intent_a[axis]))
        if center_point:
            delta = delta * 2
        middle = (
            intent_a
            if center_point
            else (
                midpoint(intent_a[0], intent_b[0]),
                midpoint(intent_a[1], intent_b[1]),
            )
        )
        centre_line = f"$sketch_1_slot_{profile_index}_centre_line"
        middle_point = f"$sketch_1_slot_{profile_index}_middle"
        dimensioned = _command(
            "sketch.draw.dimensioned",
            command=command_name,
            params={
                key_a: seed_point(intent_a),
                key_b: seed_point(intent_b),
                "width": command_value(profile.width),
            },
            dimensions={"length": command_value(delta)},
        )
        dimensioned["bind"] = {
            centre_line: "centre_line",
            middle_point: "middle",
        }
        commands.append(dimensioned)
        commands.append(
            _command(
                "sketch.constraint.horizontal_vertical",
                line=centre_line,
                mode=mode,
            )
        )
        commands.append(
            _command(
                "sketch.dimension",
                entities=["origin", middle_point],
                type="horizontal",
                value=command_value(_dim_abs(middle[0])),
            )
        )
        commands.append(
            _command(
                "sketch.dimension",
                entities=["origin", middle_point],
                type="vertical",
                value=command_value(_dim_abs(middle[1])),
            )
        )

    points = profile.points
    if profile.construction == "center_to_center":
        a, b = points
        intents = (intent(a), intent(b))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.center_to_center",
                "p0",
                a,
                "p1",
                b,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.center_to_center",
                    p0=direct_point(a),
                    p1=direct_point(b),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "overall":
        a, b = points
        intents = (intent(a), intent(b))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.overall",
                "p0",
                a,
                "p1",
                b,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.overall",
                    p0=direct_point(a),
                    p1=direct_point(b),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "center_point":
        center, end = points
        intents = (intent(center), intent(end))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.center_point",
                "center",
                center,
                "end",
                end,
                center_point=True,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.center_point",
                    center=direct_point(center),
                    end=direct_point(end),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "arc_three_point":
        start, through, end = points
        commands.append(
            _command(
                "sketch.slot.arc_three_point",
                start=direct_point(start),
                through=direct_point(through),
                end=direct_point(end),
                width=command_value(profile.width),
            )
        )
    elif profile.construction == "arc_center_end":
        center, start, end = points
        commands.append(
            _command(
                "sketch.slot.arc_center",
                center=direct_point(center),
                start=direct_point(start),
                end=direct_point(end),
                width=command_value(profile.width),
            )
        )
    elif profile.construction == "arc_center_sweep":
        center, start = points
        commands.append(
            _command(
                "sketch.slot.arc_center",
                center=direct_point(center),
                start=direct_point(start),
                width=command_value(profile.width),
                sweep=profile.sweep,
            )
        )
    else:
        raise ModelError(
            f"unsupported SlotProfileIR construction {profile.construction!r}"
        )
    return commands


def _solidcraft_axis(axis: AxisLineIR):
    """Lower semantic axis intent without losing symbolic origin dependencies."""
    if (
        isinstance(axis.direction, str)
        and all(
            not parameters_in(value) and abs(pv(value)) <= 1e-12
            for value in axis.origin
        )
    ):
        return axis.direction

    direction = (
        {
            "X": [1.0, 0.0, 0.0],
            "Y": [0.0, 1.0, 0.0],
            "Z": [0.0, 0.0, 1.0],
        }[axis.direction]
        if isinstance(axis.direction, str)
        else list(axis.direction)
    )
    return {
        "origin": [command_value(value) for value in axis.origin],
        "dir": direction,
    }


def _sketch_chain_geometry_commands(
    chain: SketchChainIR,
    *,
    model: ModelIR | None = None,
    bind_curves: bool = False,
    binding_prefix: str = "$contour_curves",
    origin_offset=(0, 0),
) -> tuple[list[dict], str | None]:
    """Lower shared semantic line/arc chain geometry without Sketch support."""
    if not isinstance(chain, SketchChainIR):
        raise ModelError("Sketch chain geometry requires SketchChainIR")
    commands = []
    curve_variable = None
    curve_count = 0
    previous_line_id = None
    line_count = 0

    def value(item):
        return (
            _role_command_value(model, item, "length")
            if model is not None
            else command_value(item)
        )

    def point(coordinates):
        shifted = (
            _solidcraft_dimension_sum(origin_offset[0], coordinates[0]),
            _solidcraft_dimension_sum(origin_offset[1], coordinates[1]),
        )
        return [value(shifted[0]), value(shifted[1])]

    def append_curve(command):
        nonlocal curve_variable, curve_count
        if bind_curves:
            curve_count += 1
            next_variable = f"{binding_prefix}_{curve_count}"
            binding = (
                "curves"
                if curve_variable is None
                else {"field": "curves", "prepend": curve_variable}
            )
            command["bind"] = {next_variable: binding}
            curve_variable = next_variable
        commands.append(command)

    for segment in chain.segments:
        if segment.kind == "line":
            line_count += 1
            line_id = f"l{line_count}"
            params = {
                "points": [point(segment.start), point(segment.end)],
                "connect": True,
            }
            if not chain.closed:
                params["ids"] = [line_id]
            append_curve(_command("sketch.line", **params))
            previous_line_id = line_id
            continue

        if segment.kind == "arc_tangent":
            if previous_line_id is None:
                raise ModelError(
                    "semantic tangent Sketch arc requires preceding line"
                )
            append_curve(
                _command(
                    "sketch.arc.tangent",
                    start=f"{previous_line_id}.end",
                    curve=previous_line_id,
                    end=point(segment.end),
                )
            )
            previous_line_id = None
            continue

        if segment.kind == "arc_three_point":
            append_curve(
                _command(
                    "sketch.arc.three_point",
                    start=point(segment.start),
                    end=point(segment.end),
                    through=point(segment.through),
                    connect=True,
                )
            )
            previous_line_id = None
            continue

        if segment.kind == "arc_center_point":
            append_curve(
                _command(
                    "sketch.arc.center_point",
                    center=point(segment.center),
                    start=point(segment.start),
                    end=point(segment.end),
                    clockwise=segment.clockwise,
                    connect=True,
                )
            )
            previous_line_id = None
            continue

        raise ModelError(
            f"unsupported semantic Sketch chain segment {segment.kind!r}"
        )

    if bind_curves and curve_variable is None:
        raise ModelError("semantic Sketch chain has no curves to consume")
    return commands, curve_variable


def _solidcraft_sketch_graph_commands(
    graph: SketchEntityGraphIR,
    *,
    sketch_index: int = 1,
    model: ModelIR | None = None,
    origin_offset=(0, 0),
) -> list[dict]:
    """Lower support-independent Sketch graph contents.

    Support creation and consuming solid features are deliberately owned by
    #561. Native/replay identities are created only in this backend.
    """
    if not isinstance(graph, SketchEntityGraphIR):
        raise TypeError("Sketch graph lowering requires SketchEntityGraphIR")
    if type(sketch_index) is not int or sketch_index < 1:
        raise ModelError("Sketch graph index must be positive")

    commands = []
    referenced_entities = {
        operation.source.index
        for operation in graph.operations
        if operation.source.kind == "entity"
    }

    def entity_variable(index):
        return f"$sketch_{sketch_index}_profile_{index + 1}"

    def operation_variable(index):
        return f"$sketch_{sketch_index}_operation_{index + 1}"

    def source_variable(reference: SketchEntityRefIR):
        if reference.kind == "entity":
            entity = graph.entities[reference.index]
            if isinstance(entity, SketchChainIR):
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            return entity_variable(reference.index)
        return operation_variable(reference.index)

    for index, entity in enumerate(graph.entities):
        variable = entity_variable(index)
        if isinstance(entity, TextEntityIR):
            _require_positive(entity.height, "sketch text height")
            rows = [
                _command(
                    "sketch.text",
                    text=entity.text,
                    at=[
                        command_value(
                            _solidcraft_dimension_sum(
                                origin_offset[index],
                                value,
                            )
                        )
                        for index, value in enumerate(entity.position)
                    ],
                    height=command_value(entity.height),
                    font=entity.font,
                )
            ]
        elif isinstance(entity, SketchChainIR):
            rows, _binding = _sketch_chain_geometry_commands(
                entity,
                model=model,
                origin_offset=origin_offset,
            )
        else:
            dummy = SketchIR(
                name="Graph",
                plane=PlaneIR("XY"),
                profiles=(entity,),
            )
            rows = _solidcraft_profile_commands(
                dummy,
                entity,
                profile_index=index + 1,
                origin_offset=origin_offset,
            )

        if index in referenced_entities:
            if isinstance(entity, SketchChainIR):
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            if not rows:
                raise ModelError(
                    "semantic Sketch entity produced no SolidCraft curves"
                )
            rows[0].setdefault("bind", {})[variable] = "curves"
        commands.extend(rows)

    for chain in graph.open_chains:
        rows, _binding = _sketch_chain_geometry_commands(
            chain,
            model=model,
            origin_offset=origin_offset,
        )
        commands.extend(rows)

    for index, operation in enumerate(graph.operations):
        source = source_variable(operation.source)
        variable = operation_variable(index)
        if isinstance(operation, SketchRectangularPatternIR):
            params = {
                "entities": source,
                "count": command_value(operation.count),
                "spacing": command_value(operation.spacing),
                "dir": list(operation.direction),
            }
            has_second_direction = (
                pv(operation.count2) != 1
                or bool(parameters_in(operation.count2))
            )
            if has_second_direction:
                params["count2"] = command_value(operation.count2)
                if operation.spacing2 is not None:
                    params["spacing2"] = command_value(operation.spacing2)
                if operation.direction2 is not None:
                    params["dir2"] = list(operation.direction2)
            if operation.alignment != "right":
                params["alignment"] = operation.alignment
            if has_second_direction and operation.alignment2 != "right":
                params["alignment2"] = operation.alignment2
            if operation.reversed:
                params["reversed"] = True
            if has_second_direction and operation.reversed2:
                params["reversed2"] = True
            row = _command("sketch.pattern.rectangular", **params)
            row["bind"] = {
                variable: {
                    "field": "curves",
                    "prepend": source,
                }
            }
        elif isinstance(operation, SketchMirrorIR):
            row = _command(
                "sketch.mirror",
                entities=source,
                line=operation.axis,
            )
            row["bind"] = {variable: "curves"}
        else:
            raise ModelError(
                f"unsupported Sketch operation IR {type(operation).__name__}"
            )
        commands.append(row)

    return commands
