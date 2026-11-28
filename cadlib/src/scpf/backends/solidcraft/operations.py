"""SolidCraft lowering for body operations and modifiers."""
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
from .primitives import _box_command, _csg_primitive_command
from .features import _typed_rectangular_base
from .sketch import (
    _principal_plane_offset,
    _solidcraft_sketch_create,
    _solidcraft_sketch_support_commands,
    _next_sketch_index,
    _solidcraft_relation_polygon_points,
    _solidcraft_profile_commands,
    _solidcraft_sketch_graph_commands,
    _solidcraft_axis,
)

_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}


def _body_commands(*args, **kwargs):
    from .dispatch import body_commands
    return body_commands(*args, **kwargs)


def _fillet_commands(model: ModelIR, node: FilletIR, name: str) -> list[dict]:
    """Lower one constant-radius FilletIR through shared selector semantics."""
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft FilletIR requires typed BodyIR base")

    base_commands = _body_commands(model, node.base, name)
    topology, edges = _edge_selection_commands(
        node.base,
        node.edges,
        name,
        prior=base_commands,
    )

    radius = _require_positive(node.radius, "fillet radius")
    if isinstance(node.edges, ParallelEdgeSetIR):
        if node.edges.axis != "Z":
            raise ModelError(
                "portable SolidCraft parallel-edge selection currently requires Z"
            )
        width, depth, _corner, _center, _height = _typed_rectangular_base(
            node.base
        )
        if radius * 2 >= min(pv(width), pv(depth)):
            raise ModelError("fillet radius exceeds rectangular base dimensions")

    return [
        *base_commands,
        *topology,
        _command(
            "solid.fillet",
            edges=edges,
            radius=command_value(node.radius),
            body=name,
        ),
    ]


def _translated_body_ir(
    node: BodyIR,
    offset: tuple,
) -> BodyIR:
    """Apply one semantic translation through the current typed CSG tree."""
    if isinstance(node, TranslationIR):
        combined = tuple(
            _dim_add(node.offset[index], offset[index])
            for index in range(3)
        )
        return _translated_body_ir(node.body, combined)
    if isinstance(node, PlacementIR):
        return PlacementIR(
            primitive=node.primitive,
            point=tuple(
                _dim_add(node.point[index], offset[index])
                for index in range(3)
            ),
            anchor=node.anchor,
            explicit=True,
        )
    if isinstance(node, BooleanIR):
        return BooleanIR(
            operation=node.operation,
            target=_translated_body_ir(node.target, offset),
            tool=_translated_body_ir(node.tool, offset),
        )
    raise ModelError(
        "portable SolidCraft TranslationIR supports primitive/Boolean CSG bodies"
    )


def _csg_style_tool(node: BodyIR) -> bool:
    """Return whether a tool belongs to the stable primitive CSG spelling."""
    if isinstance(node, TranslationIR):
        return _csg_style_tool(node.body)
    return (
        isinstance(node, PlacementIR)
        or (
            isinstance(node, BooleanIR)
            and node.operation == "join"
        )
    )


def _boolean_tool_commands(
    model: ModelIR,
    node: BodyIR,
    name: str,
    operation: str,
    *,
    prior: list[dict],
) -> list[dict]:
    """Apply one typed Boolean tool to an existing native body."""
    if isinstance(node, TranslationIR):
        return _boolean_tool_commands(
            model,
            _translated_body_ir(node.body, node.offset),
            name,
            operation,
            prior=prior,
        )
    if isinstance(node, PlacementIR):
        return [
            *prior,
            _csg_primitive_command(node, name, operation),
        ]
    if isinstance(node, ExtrudeIR):
        return _extrude_commands(
            model,
            node,
            name,
            operation_override=operation,
            prior=prior,
        )
    if isinstance(node, RevolveIR):
        return _revolve_commands(
            model,
            node,
            name,
            operation_override=operation,
            prior=prior,
        )
    if (
        isinstance(node, BooleanIR)
        and node.operation == "join"
        and operation in {"join", "cut"}
    ):
        commands = _boolean_tool_commands(
            model,
            node.target,
            name,
            operation,
            prior=prior,
        )
        return _boolean_tool_commands(
            model,
            node.tool,
            name,
            operation,
            prior=commands,
        )
    raise ModelError(
        "portable SolidCraft BooleanIR has no qualified lowering for tool "
        f"{type(node).__name__}"
    )


def _boolean_commands(model: ModelIR, node: BooleanIR, name: str) -> list[dict]:
    """Lower generic BooleanIR while keeping backend tool support explicit."""
    if not isinstance(node.target, BodyIR) or not isinstance(node.tool, BodyIR):
        raise ModelError("portable SolidCraft BooleanIR requires typed body operands")

    if isinstance(node.target, PlacementIR):
        primitive_csg_tool = _csg_style_tool(node.tool)
        commands = (
            [_csg_primitive_command(node.target, name, "new")]
            if primitive_csg_tool
            else _body_commands(model, node.target, name)
        )
    elif isinstance(node.target, BooleanIR):
        commands = _boolean_commands(model, node.target, name)
    else:
        commands = _body_commands(model, node.target, name)

    return _boolean_tool_commands(
        model,
        node.tool,
        name,
        node.operation,
        prior=commands,
    )


_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}


def _extrude_commands(
    model: ModelIR,
    node: ExtrudeIR,
    name: str,
    *,
    operation_override: str | None = None,
    prior: list[dict] | None = None,
) -> list[dict]:
    """Lower typed Sketch/Extrude semantics, optionally as one CSG tool."""
    sketch = node.sketch
    if not isinstance(sketch, SketchIR):
        raise ModelError("portable SolidCraft ExtrudeIR requires SketchIR")

    if operation_override is not None and (
        operation_override not in {"join", "cut", "intersect"}
        or node.operation != "new_body"
        or node.target is not None
        or sketch.support is not None
    ):
        raise ModelError(
            "Boolean ExtrudeIR tool requires one standalone new-body ExtrudeIR"
        )

    commands = list(prior or [])
    if operation_override is None and node.operation != "new_body":
        if not isinstance(node.target, BodyIR):
            raise ModelError("attached ExtrudeIR requires typed body target")
        commands.extend(_body_commands(model, node.target, name))

    support_commands, local_origin = _solidcraft_sketch_support_commands(
        sketch,
        name,
        prior=commands,
    )
    sketch_index = _next_sketch_index(commands)
    commands.extend(support_commands)

    if sketch.graph is not None:
        commands.extend(
            _solidcraft_sketch_graph_commands(
                sketch.graph,
                sketch_index=sketch_index,
                model=model,
                origin_offset=local_origin,
            )
        )
    else:
        for index, profile in enumerate(sketch.profiles, start=1):
            commands.extend(
                _solidcraft_profile_commands(
                    sketch,
                    profile,
                    profile_index=index,
                    origin_offset=local_origin,
                )
            )
    commands.append(_command("sketch.finish"))

    params = {"direction": node.direction}
    effective_operation = operation_override or node.operation
    if effective_operation == "new_body":
        params["body_name"] = name
    else:
        params["operation"] = effective_operation
        params["targets"] = [name]
        if operation_override is None:
            params["name"] = sketch.name

    if node.through_all:
        params["through_all"] = True
    else:
        _require_positive(node.distance, "sketch extrusion distance")
        params["distance"] = _role_command_value(
            model,
            node.distance,
            "length",
        )

    if node.regions:
        # A single direct profile with no authored selector keeps the stable
        # implicit all-profile spelling.
        implicit_single = (
            len(node.regions) == 1
            and node.regions[0].selector is None
            and len(sketch.profiles) == 1
            and sketch.graph is not None
            and len(sketch.graph.entities) == 1
            and not sketch.graph.operations
        )
        if not implicit_single:
            picks = []
            exact = False
            for region in node.regions:
                try:
                    pick = _region_interior_point(sketch, region)
                except ValueError as exc:
                    raise ModelError(str(exc)) from exc
                picks.append({"point": [pick[0], pick[1]]})
                exact = exact or region.exact or region.selector is None
            params["profiles"] = picks
            if exact:
                params["exact_regions"] = True

    commands.append(_command("solid.extrude", **params))
    return commands


def _revolve_commands(
    model: ModelIR,
    node: RevolveIR,
    name: str,
    *,
    operation_override: str | None = None,
    prior: list[dict] | None = None,
) -> list[dict]:
    """Lower semantic RevolveIR from the completed typed Sketch graph."""
    sketch = node.sketch
    _principal_plane_offset(
        sketch.plane,
        label="portable SolidCraft RevolveIR",
    )
    if (
        sketch.support is not None
        or sketch.rotation is not None
        or sketch.graph is None
        or len(sketch.graph.entities) != 1
    ):
        raise ModelError(
            "portable SolidCraft RevolveIR requires one standalone "
            "unrotated authored Sketch profile"
        )
    if not isinstance(node.axis, AxisLineIR):
        raise ModelError("portable SolidCraft RevolveIR requires AxisLineIR")

    sweep = pv(node.angle)
    if not isfinite(sweep) or sweep <= 0 or sweep > 360:
        raise ModelError(
            "sketch revolve angle must be above 0 and at most 360 degrees"
        )

    if operation_override is not None and (
        operation_override not in {"join", "cut", "intersect"}
        or node.operation != "new_body"
        or node.target is not None
    ):
        raise ModelError(
            "Boolean RevolveIR tool requires one standalone new-body RevolveIR"
        )

    revolve = {
        "sketch": sketch.name,
        "axis": _solidcraft_axis(node.axis),
        "angle": _role_command_value(model, node.angle, "angle"),
    }
    if node.direction is not None:
        revolve["direction"] = node.direction

    effective_operation = operation_override or node.operation
    base_commands = list(prior or [])
    if effective_operation == "new_body":
        if node.target is not None:
            raise ModelError("new-body RevolveIR must not have a target")
        revolve["body_name"] = name
    elif operation_override is not None:
        revolve["operation"] = effective_operation
        revolve["targets"] = [name]
    elif effective_operation == "cut":
        if (
            not isinstance(node.target, PlacementIR)
            or not isinstance(node.target.primitive, BoxIR)
        ):
            raise ModelError(
                "portable SolidCraft Revolve cut currently requires a Box target"
            )
        base_commands = [_box_command(node.target, name)]
        revolve["operation"] = "cut"
        revolve["targets"] = [name]
    else:
        raise ModelError(
            f"unsupported portable SolidCraft Revolve operation {effective_operation!r}"
        )

    sketch_index = _next_sketch_index(base_commands)
    sketch_commands = [_solidcraft_sketch_create(sketch)]
    entity = sketch.graph.entities[0]
    if isinstance(entity, PolygonProfileIR):
        relation_points = _solidcraft_relation_polygon_points(sketch)
        authored_points = (
            relation_points
            if relation_points is not None
            else entity.points
        )
        ids = (
            list(entity.segment_ids)
            if entity.segment_ids is not None
            else [
                chr(ord("a") + index)
                for index in range(len(authored_points))
            ]
        )
        sketch_commands.append(
            _command(
                "sketch.line",
                points=[
                    [
                        _role_command_value(model, value, "length")
                        for value in point
                    ]
                    for point in authored_points
                ],
                closed=True,
                ids=ids,
            )
        )
    else:
        sketch_commands.extend(
            _solidcraft_sketch_graph_commands(
                sketch.graph,
                sketch_index=sketch_index,
                model=model,
            )
        )
    sketch_commands.append(_command("sketch.finish"))

    return [
        *base_commands,
        *sketch_commands,
        _command("solid.revolve", **revolve),
    ]


def _next_face_query_index(commands: list[dict]) -> int:
    return 1 + sum(
        command.get("command") == "model.faces"
        for command in commands
    )


def _face_query_command(
    name: str,
    face: str,
    variable: str,
    *,
    select: str | None = None,
) -> dict:
    try:
        normal = _FACE_NORMALS[face]
    except KeyError as exc:
        raise ModelError(
            f"unsupported Forge face in IR: {face!r}"
        ) from exc
    selector = {
        "field": "faces",
        "where": {"plane_normal": normal},
        "max": "area",
    }
    if select is not None:
        selector["select"] = select
    command = _command("model.faces", body=name)
    command["bind"] = {variable: selector}
    return command


def _face_boundary_commands(
    selection: FaceBoundaryIR,
    name: str,
    *,
    prior: list[dict] | None = None,
) -> tuple[list[dict], str]:
    if not selection.faces:
        raise ModelError("portable SolidCraft face-boundary IR has no faces")

    commands = []
    previous_edges = None
    start = _next_face_query_index(prior or [])
    for offset, face in enumerate(selection.faces):
        index = start + offset
        face_variable = f"$topology_face_{index}"
        edge_variable = f"$topology_edges_{index}"
        commands.append(_face_query_command(name, face, face_variable))
        binding = {
            "field": "edges",
            "body": name,
            "boundary_of": face_variable,
        }
        if previous_edges is not None:
            binding["prepend"] = previous_edges
        commands.append(
            {
                "command": "model.edges",
                "params": {"body": name},
                "bind": {edge_variable: binding},
            }
        )
        previous_edges = edge_variable

    return commands, previous_edges


def _rectangular_edge_picks(
    base: BodyIR,
    vectors: tuple[tuple[int, int, int], ...],
) -> list[list[float]]:
    """Derive stable SolidCraft edge picks from typed rectangular-body semantics."""
    width, depth, corner, _center, height = _typed_rectangular_base(base)
    dimensions = (width, depth, height)
    picks = []
    for vector in vectors:
        point = []
        for minimum, dimension, side in zip(corner, dimensions, vector):
            if side < 0:
                value = minimum
            elif side > 0:
                value = _combine(minimum, dimension)
            else:
                value = _combine(minimum, half(dimension))
            point.append(pv(value))
        if not all(isfinite(value) for value in point):
            raise ModelError("rectangular edge selection must be finite")
        picks.append(point)
    return picks


def _profile_source_extrude(base: BodyIR) -> ExtrudeIR | None:
    """Find the authored profile source through stable modifier history."""
    while isinstance(base, (FilletIR, ChamferIR, ShellIR)):
        base = base.base
    return base if isinstance(base, ExtrudeIR) else None


def _profile_edge_picks(
    base: BodyIR,
    selection: ProfileEdgeSetIR,
) -> list[list[float]]:
    """Derive named Polygon-extrusion edge picks from semantic profile intent."""
    source = _profile_source_extrude(base)
    if (
        source is None
        or source.operation != "new_body"
        or source.through_all
        or source.distance is None
        or source.sketch.support is not None
        or source.sketch.plane.orientation != "XZ"
        or len(source.sketch.profiles) != 1
        or not isinstance(source.sketch.profiles[0], PolygonProfileIR)
    ):
        raise ModelError(
            "named profile edges require a standalone XZ polygon extrusion"
        )

    profile = source.sketch.profiles[0]
    names = profile.segment_ids
    if names is None:
        raise ModelError(
            "Polygon2D must define ids= or named points to select profile edges"
        )
    for pattern in selection.patterns:
        if not any(fnmatchcase(label, pattern) for label in names):
            raise ModelError(
                f"no polygon segment or vertex matches {pattern!r}"
            )

    matches = [
        index
        for index, label in enumerate(names)
        if any(
            fnmatchcase(label, pattern)
            for pattern in selection.patterns
        )
    ]
    plane_y = source.sketch.plane.origin[1]
    thickness = source.distance
    if source.direction == "symmetric":
        start_y = _combine(plane_y, -half(thickness))
        end_y = _combine(plane_y, half(thickness))
    elif source.direction == "positive":
        start_y = plane_y
        end_y = _combine(plane_y, thickness)
    elif source.direction == "negative":
        start_y = plane_y
        end_y = _combine(plane_y, -thickness)
    else:
        raise ModelError(
            "named profile edges require finite positive/negative/symmetric Extrude"
        )

    points = profile.points
    if selection.kind == "vertices":
        sweep_mid_y = midpoint(pv(start_y), pv(end_y))
        return [
            [pv(points[index][0]), sweep_mid_y, -pv(points[index][1])]
            for index in matches
        ]

    if selection.kind != "segments":
        raise ModelError(
            f"unsupported profile edge selection: {selection.kind}"
        )

    picks = []
    for y in (start_y, end_y):
        for index in matches:
            first = points[index]
            second = points[(index + 1) % len(points)]
            picks.append(
                [
                    midpoint(pv(first[0]), pv(second[0])),
                    pv(y),
                    -midpoint(pv(first[1]), pv(second[1])),
                ]
            )
    return picks


def _edge_selection_commands(
    base: BodyIR,
    selection,
    name: str,
    *,
    prior: list[dict] | None = None,
) -> tuple[list[dict], list[list[float]] | str]:
    """Lower shared semantic edge-selection intent to SolidCraft transport."""
    if isinstance(selection, FaceBoundaryIR):
        return _face_boundary_commands(
            selection,
            name,
            prior=prior,
        )

    if isinstance(selection, ParallelEdgeSetIR):
        if selection.axis != "Z":
            raise ModelError(
                "portable SolidCraft parallel-edge selection currently requires Z"
            )
        return [], _rectangular_edge_picks(
            base,
            (
                (-1, -1, 0),
                (1, -1, 0),
                (1, 1, 0),
                (-1, 1, 0),
            ),
        )

    if isinstance(selection, DirectionPairEdgeSetIR):
        return [], _rectangular_edge_picks(base, selection.vectors)

    if isinstance(selection, ProfileEdgeSetIR):
        return [], _profile_edge_picks(base, selection)

    if isinstance(selection, ExplicitEdgePicksIR):
        picks = [
            [pv(value) for value in point]
            for point in selection.points
        ]
        if not all(isfinite(value) for point in picks for value in point):
            raise ModelError("edge selection must be finite")
        return [], picks

    raise ModelError(
        f"unsupported portable SolidCraft edge selector {type(selection).__name__}"
    )


def _face_name_commands(
    prior: list[dict],
    selection: FaceSetIR,
    name: str,
) -> tuple[list[dict], list[str]]:
    if not isinstance(selection, FaceSetIR):
        raise ModelError("portable SolidCraft shell requires FaceSetIR")
    commands = []
    variables = []
    start = _next_face_query_index(prior)
    for offset, face in enumerate(selection.faces):
        variable = f"$topology_face_name_{start + offset}"
        commands.append(
            _face_query_command(
                name,
                face,
                variable,
                select="name",
            )
        )
        variables.append(variable)
    return commands, variables


def _chamfer_commands(model: ModelIR, node: ChamferIR, name: str) -> list[dict]:
    """Lower ChamferIR through the same shared semantic selector vocabulary."""
    _require_positive(node.distance, "chamfer distance")
    if node.distance2 is not None:
        _require_positive(node.distance2, "chamfer distance2")
    if node.flip and node.distance2 is None:
        raise ModelError("portable SolidCraft ChamferIR flip requires distance2")
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft ChamferIR requires typed BodyIR base")

    base_commands = _body_commands(model, node.base, name)
    topology, edges = _edge_selection_commands(
        node.base,
        node.edges,
        name,
        prior=base_commands,
    )
    params = {
        "body": name,
        "distance": command_value(node.distance),
        "edges": edges,
    }
    if node.distance2 is not None:
        params["distance2"] = command_value(node.distance2)
    if node.flip:
        params["flip"] = True

    return [
        *base_commands,
        *topology,
        _command("solid.chamfer", **params),
    ]


def _shell_commands(model: ModelIR, node: ShellIR, name: str) -> list[dict]:
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft ShellIR requires typed BodyIR base")
    _require_positive(node.thickness, "shell thickness")
    base_commands = _body_commands(model, node.base, name)
    topology, faces = _face_name_commands(
        base_commands,
        node.open_faces,
        name,
    )
    return [
        *base_commands,
        *topology,
        _command(
            "solid.shell",
            faces=faces,
            thickness=command_value(node.thickness),
            body=name,
        ),
    ]


_AUTO_TYPED_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.extrude": "Extrude",
    "solid.hole": "Hole",
}
