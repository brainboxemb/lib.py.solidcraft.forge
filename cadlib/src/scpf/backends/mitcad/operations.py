"""Mitcad lowering for body operations, modifiers and translations."""
from __future__ import annotations

from math import isfinite

from ...compiler import ModelError, _require_positive
from ...core import (
    Expression,
    Parameter,
    Shape,
    _DirectionSelector,
    _dim_add,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    _sphere_center_from_anchor,
    command_value,
    number_text,
    parameters_in,
)
from ...ir import (
    AxisLineIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FeatureRefIR,
    FilletIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    SketchRelationsIR,
    SphereIR,
    SuppressionColumnIR,
    TranslationIR,
    _region_interior_point,
    normalize_shape,
    resolve_feature_ref,
)
from ...scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


from .common import _parameter_commands, _role_command_value
from .primitives import _box_command, _csg_primitive_commands
from .configuration import _mitcad_configuration_commands
from .sketch import (
    _mitcad_sketch_plane,
    _sketch_relations_transport,
    _mitcad_revolve_axis,
)

FORMAT = "scpf-mitcad"
VERSION = 1

_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}


def _boolean_command_plan(
    node: BooleanIR,
    name: str,
    *,
    path: tuple[str, ...] = ("root",),
) -> tuple[list[dict], dict[tuple[str, ...], int]]:
    """Lower Boolean history and map semantic paths to native feature commands."""
    commands: list[dict] = []
    feature_indexes: dict[tuple[str, ...], int] = {}

    target_path = (*path, "target")
    if isinstance(node.target, BooleanIR):
        target_commands, target_indexes = _boolean_command_plan(
            node.target,
            name,
            path=target_path,
        )
        commands.extend(target_commands)
        feature_indexes.update(target_indexes)
    elif isinstance(node.target, PlacementIR):
        target_commands, relative_feature = _csg_primitive_commands(
            node.target,
            f"{name}Base",
            "new_body",
            path=target_path,
        )
        start = len(commands)
        commands.extend(target_commands)
        feature_indexes[target_path] = start + relative_feature
    else:
        raise ModelError("Mitcad BooleanIR has unsupported target")

    tool_path = (*path, "tool")
    if not isinstance(node.tool, PlacementIR):
        raise ModelError(
            "Mitcad BooleanIR has unsupported typed tool "
            f"{type(node.tool).__name__}"
        )
    tool_commands, relative_feature = _csg_primitive_commands(
        node.tool,
        f"{name}{node.operation.title()}{len(commands)}",
        node.operation,
        path=tool_path,
    )
    start = len(commands)
    commands.extend(tool_commands)
    feature_index = start + relative_feature
    feature_indexes[tool_path] = feature_index
    # The Boolean operation itself is authored by the tool feature command.
    feature_indexes[path] = feature_index

    return commands, feature_indexes


def _boolean_commands(node: BooleanIR, name: str) -> list[dict]:
    """Return native Boolean commands without exposing helper-layout metadata."""
    return _boolean_command_plan(node, name)[0]


def _boolean_feature_command_index(
    root: BooleanIR,
    reference: FeatureRefIR,
) -> int:
    """Map semantic FeatureRefIR to the native semantic feature command."""
    resolve_feature_ref(root, reference)
    _commands, feature_indexes = _boolean_command_plan(
        root,
        "FeatureLayout",
    )
    try:
        return feature_indexes[reference.path]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad semantic feature path {reference.path!r} has no native feature"
        ) from exc


_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}


def _extrude_commands(
    node: ExtrudeIR,
    name: str,
) -> list[dict]:
    """Lower semantic Sketch/Profile + Extrude IR to native Mitcad features."""
    sketch = node.sketch
    plane_commands, native_plane = _mitcad_sketch_plane(sketch.plane)
    if len(node.regions) != 1:
        raise ModelError("Mitcad Extrude IR requires one region")

    region = node.regions[0]
    if not isinstance(region, RegionIR):
        raise ModelError("Mitcad Extrude IR requires RegionIR")
    try:
        pick = _region_interior_point(sketch, region)
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    _require_positive(node.distance, "sketch extrusion distance")
    entities = []
    dimensions = []

    polygon = (
        len(sketch.profiles) == 1
        and isinstance(sketch.profiles[0], PolygonProfileIR)
    )
    if polygon:
        if node.direction != "symmetric":
            raise ModelError(
                "Mitcad PolygonProfileIR currently requires symmetric extrusion"
            )
        profile = sketch.profiles[0]
        parameterized = any(
            parameters_in(value)
            for point in profile.points
            for value in point
        )
        if sketch.relations is not None:
            entities, constraints, dimensions = _sketch_relations_transport(
                sketch.relations
            )
        elif parameterized:
            raise ModelError(
                "parameterized Mitcad Polygon Extrude requires typed Sketch relations"
            )
        else:
            constraints = []
            point_ids = []
            for index, point in enumerate(profile.points, start=1):
                point_id = f"p{index}"
                point_ids.append(point_id)
                entities.append(
                    {
                        "id": point_id,
                        "type": "point",
                        "at": [pv(value) for value in point],
                        "fixed": True,
                    }
                )

            first_curve = len(point_ids) + 1
            for offset, start_id in enumerate(point_ids):
                end_id = point_ids[(offset + 1) % len(point_ids)]
                entities.append(
                    {
                        "id": f"c{first_curve + offset}",
                        "type": "line",
                        "start": start_id,
                        "end": end_id,
                    }
                )

        selector = [pick[0], pick[1]]
        extent = {
            "type": "symmetric",
            "distance": command_value(node.distance),
            "full_length": True,
        }
    else:
        if node.direction not in ("positive", "negative"):
            raise ModelError(
                "Mitcad circle Extrude IR requires positive or negative direction"
            )

        profiles = []
        for profile in sketch.profiles:
            if not isinstance(profile, CircleProfileIR):
                raise ModelError(
                    "Mitcad Extrude IR requires one qualified profile family"
                )
            if any(
                parameters_in(value) or pv(value) != 0
                for value in profile.center
            ):
                raise ModelError(
                    "Mitcad CircleProfileIR currently requires origin center"
                )
            _require_positive(profile.diameter, "circle diameter")
            profiles.append(profile)

        center = [
            command_value(value)
            for value in profiles[0].center
        ]
        entities.append(
            {
                "id": "p1",
                "type": "point",
                "at": center,
                "fixed": True,
            }
        )
        for index, profile in enumerate(profiles, start=2):
            curve = f"c{index}"
            entities.append(
                {
                    "id": curve,
                    "type": "circle",
                    "center": "p1",
                    "radius": pv(profile.diameter) / 2.0,
                }
            )
            dimensions.append(
                {
                    "id": f"k{index - 1}",
                    "type": "diameter",
                    "curve": curve,
                    "value": command_value(profile.diameter),
                }
            )

        selector = (
            center
            if len(sketch.profiles) == 1
            else [pick[0], pick[1]]
        )
        extent = {
            "type": "distance",
            "distance": command_value(
                -node.distance
                if node.direction == "negative"
                else node.distance
            ),
        }

    sketch_definition = {
        "type": "sketch",
        "plane": native_plane,
        "entities": entities,
        "constraints": constraints if polygon else [],
        "dimensions": dimensions,
    }
    extrude_definition = {
        "type": "extrude",
        "profiles": [
            {
                "sketch": {"ref": "sk.uid"},
                "point": selector,
            }
        ],
        "extent": extent,
        "flip": False,
        "operation": "new_body",
        "participants": [],
    }
    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "as": "sk",
            "name": sketch.name,
            "def": sketch_definition,
        },
        {
            "cmd": "add_feature",
            "name": name,
            "def": extrude_definition,
        },
    ]


def _revolve_commands(
    model: ModelIR,
    node: RevolveIR,
    name: str,
    *,
    participant=None,
    feature_binding: str | None = None,
) -> list[dict]:
    """Lower semantic RevolveIR to native Mitcad Sketch + Revolve."""
    sketch = node.sketch
    plane_commands, native_plane = _mitcad_sketch_plane(sketch.plane)
    if (
        len(sketch.profiles) != 1
        or not isinstance(sketch.profiles[0], PolygonProfileIR)
        or node.region != RegionIR(outer=0)
    ):
        raise ModelError("Mitcad RevolveIR requires one polygon region")
    if not isinstance(node.axis, AxisLineIR) or node.direction is not None:
        raise ModelError(
            "Mitcad RevolveIR requires one non-symmetric AxisLineIR"
        )
    if node.operation == "new_body":
        if node.target is not None or participant is not None:
            raise ModelError("new-body Mitcad RevolveIR must not have a target")
    elif node.operation == "cut":
        if (
            not isinstance(node.target, PlacementIR)
            or not isinstance(node.target.primitive, BoxIR)
            or participant is None
        ):
            raise ModelError(
                "Mitcad Revolve cut currently requires one bound Box participant"
            )
    else:
        raise ModelError(
            f"unsupported Mitcad Revolve operation {node.operation!r}"
        )

    try:
        pick = _region_interior_point(sketch, node.region)
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    sweep = pv(node.angle)
    if not isfinite(sweep) or sweep <= 0 or sweep > 360:
        raise ModelError(
            "sketch revolve angle must be above 0 and at most 360 degrees"
        )

    profile = sketch.profiles[0]
    parameterized = any(
        parameters_in(value)
        for point in profile.points
        for value in point
    )
    if sketch.relations is not None:
        entities, constraints, dimensions = _sketch_relations_transport(
            sketch.relations,
            model=model,
        )
    elif parameterized:
        raise ModelError(
            "parameterized Mitcad Polygon Revolve requires typed Sketch relations"
        )
    else:
        point_ids = []
        entities = []
        for index, point in enumerate(profile.points, start=1):
            point_id = f"p{index}"
            point_ids.append(point_id)
            entities.append({
                "id": point_id,
                "type": "point",
                "at": [pv(value) for value in point],
                "fixed": True,
            })
        first_curve = len(point_ids) + 1
        for offset, start_id in enumerate(point_ids):
            end_id = point_ids[(offset + 1) % len(point_ids)]
            entities.append({
                "id": f"c{first_curve + offset}",
                "type": "line",
                "start": start_id,
                "end": end_id,
            })
        constraints = []
        dimensions = []

    native_axis = _mitcad_revolve_axis(
        node,
        entities,
        constraints,
        dimensions,
    )

    if parameters_in(node.angle):
        extent = {
            "type": "angle",
            "angle": _role_command_value(model, node.angle, "angle"),
        }
    elif abs(sweep - 360.0) <= 1e-12:
        extent = {"type": "full"}
    else:
        extent = {"type": "angle", "angle": f"{number_text(sweep)} deg"}

    revolve_definition = {
        "type": "revolve",
        "profiles": [{
            "sketch": {"ref": "sk.uid"},
            "point": [pick[0], pick[1]],
        }],
        "axis": native_axis,
        "extent": extent,
        "operation": node.operation,
    }
    if node.operation == "cut":
        revolve_definition["participants"] = [participant]

    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "as": "sk",
            "name": sketch.name,
            "def": {
                "type": "sketch",
                "plane": native_plane,
                "entities": entities,
                "constraints": constraints,
                "dimensions": dimensions,
            },
        },
        {
            **({"as": feature_binding} if feature_binding is not None else {}),
            "cmd": "add_feature",
            "name": name,
            "def": revolve_definition,
        },
    ]


def _revolve_cut_document(
    model: ModelIR,
    node: RevolveIR,
    name: str,
):
    """Bind the existing target body at runtime before one native Revolve cut."""
    if (
        node.operation != "cut"
        or not isinstance(node.target, PlacementIR)
        or not isinstance(node.target.primitive, BoxIR)
    ):
        raise ModelError(
            "Mitcad Revolve cut currently requires one typed Box target"
        )

    commands = [
        *_parameter_commands(model),
        _box_command(node.target, f"{name}Base"),
    ]
    feature_binding = (
        "configured_feature"
        if model.configuration is not None
        else None
    )
    replay_commands = _revolve_commands(
        model,
        node,
        name,
        participant={"$mitcad_bind": "body"},
        feature_binding=feature_binding,
    )
    if model.configuration is not None:
        replay_commands.extend(
            _mitcad_configuration_commands(
                model,
                model.configuration,
                feature_binding=feature_binding,
            )
        )
    replay = [
        {
            "bind_single_body": "body",
            "commands": replay_commands,
        }
    ]
    dependencies = _native_dependencies((commands, replay))
    return {
        "format": FORMAT,
        "version": VERSION,
        "backend": "mitcad",
        "commands": _plain_command_value(commands),
        "replay": _plain_command_value(replay),
    }, dependencies


def _fillet_document(
    model: ModelIR,
    node: FilletIR,
    name: str,
    *,
    tool: PlacementIR | None = None,
):
    """Lower semantic Fillet through replay-bound native topology."""
    if (
        not isinstance(node.base, PlacementIR)
        or not isinstance(node.base.primitive, BoxIR)
    ):
        raise ModelError("Mitcad FilletIR currently requires a Box base")

    if isinstance(node.edges, ParallelEdgeSetIR):
        if node.edges.axis != "Z":
            raise ModelError(
                "Mitcad FilletIR parallel edges currently require Z"
            )
        edge_binding_name = "parallel_edges"
        edge_binding_key = "bind_parallel_edges"
        edge_binding = {
            "name": edge_binding_name,
            "body": "body",
            "axis": node.edges.axis,
            "expected": 4,
        }
    elif isinstance(node.edges, FaceBoundaryIR):
        if node.edges.faces != ("top",):
            raise ModelError(
                "Mitcad FilletIR face boundary currently requires TOP"
            )
        edge_binding_name = "edges"
        edge_binding_key = "bind_face_boundary_edges"
        edge_binding = {
            "name": edge_binding_name,
            "body": "body",
            "face": {
                "surface": "plane",
                "normal": _FACE_NORMALS["top"],
                "normal_tolerance": 1e-6,
            },
        }
    else:
        raise ModelError("Mitcad FilletIR has unsupported edge semantics")

    _require_positive(node.radius, "fillet radius")
    if model.configuration is not None:
        raise ModelError(
            "Mitcad FilletIR configuration is outside the qualified slice"
        )

    commands = [
        *_parameter_commands(model),
        _box_command(node.base, f"{name}Base"),
    ]
    replay_commands = [
        {
            "cmd": "add_feature",
            "name": f"{name}Fillet" if tool is not None else name,
            "def": {
                "type": "fillet",
                "body": {"$mitcad_bind": "body"},
                "edges": {"$mitcad_bind": edge_binding_name},
                "radius": command_value(node.radius),
            },
        }
    ]

    if tool is not None:
        if not isinstance(node.edges, ParallelEdgeSetIR):
            raise ModelError(
                "Mitcad face-boundary FilletIR remains standalone"
            )
        if not isinstance(tool.primitive, ConeIR):
            raise ModelError(
                "Mitcad FilletIR Boolean composition currently requires ConeIR"
            )
        tool_commands, _feature_index = _csg_primitive_commands(
            tool,
            f"{name}Join",
            "join",
            path=("root", "tool"),
        )
        replay_commands.extend(tool_commands)

    replay_stage = {
        "bind_single_body": "body",
        edge_binding_key: edge_binding,
        "commands": replay_commands,
    }
    replay = [replay_stage]
    dependencies = _native_dependencies((commands, replay))
    return {
        "format": FORMAT,
        "version": VERSION,
        "backend": "mitcad",
        "commands": _plain_command_value(commands),
        "replay": _plain_command_value(replay),
    }, dependencies


def _chamfer_document(
    model: ModelIR,
    node: ChamferIR,
    name: str,
):
    _require_positive(node.distance, "chamfer distance")
    if node.distance2 is not None:
        _require_positive(node.distance2, "chamfer distance2")
    if node.flip and node.distance2 is None:
        raise ModelError("Mitcad ChamferIR flip requires distance2")
    if not isinstance(node.edges, FaceBoundaryIR):
        raise ModelError(
            "Mitcad ChamferIR currently supports FaceBoundaryIR selectors only"
        )
    if not node.edges.faces:
        raise ModelError("Mitcad face-boundary chamfer has no Faces values")

    asymmetric = node.distance2 is not None
    if asymmetric and node.edges.faces != ("top",):
        raise ModelError(
            "Mitcad asymmetric ChamferIR currently requires one TOP face boundary"
        )

    face_queries = []
    for face in node.edges.faces:
        try:
            normal = _FACE_NORMALS[face]
        except KeyError as exc:
            raise ModelError(
                f"Mitcad backend does not support Forge face {face!r}"
            ) from exc
        face_queries.append(
            {
                "surface": "plane",
                "normal": normal,
                "normal_tolerance": 1e-6,
            }
        )

    if isinstance(node.base, PlacementIR):
        if not isinstance(node.base.primitive, BoxIR):
            raise ModelError(
                "Mitcad ChamferIR placement base currently requires BoxIR"
            )
        base_commands = [_box_command(node.base, f"{name}Base")]
    elif isinstance(node.base, ExtrudeIR):
        if asymmetric or node.flip:
            raise ModelError(
                "Mitcad asymmetric ChamferIR currently requires a BoxIR base"
            )
        base_commands = _extrude_commands(node.base, f"{name}Base")
    else:
        raise ModelError("Mitcad ChamferIR has unsupported typed base")

    boundary = {
        "name": "edges",
        "body": "body",
    }
    if len(face_queries) == 1:
        # Keep the already-qualified v1 transport spelling stable.
        boundary["face"] = face_queries[0]
    else:
        boundary["faces"] = face_queries

    if asymmetric:
        # Native v0.70.0 needs the actual selected face name to orient
        # two-distance chamfer deterministically. This binding is replay-only
        # backend transport; the semantic IR still contains Faces.TOP.
        boundary["face_name"] = "reference_face"
        size = {
            "type": "two_distances",
            "distance1": command_value(node.distance),
            "distance2": command_value(node.distance2),
        }
        chamfer_set = {
            "edges": {"$mitcad_bind": "edges"},
            "size": size,
            "reference_face": {"$mitcad_bind": "reference_face"},
        }
        if node.flip:
            chamfer_set["flip"] = True
        chamfer_def = {
            "type": "chamfer",
            "body": {"$mitcad_bind": "body"},
            "sets": [chamfer_set],
        }
    else:
        chamfer_def = {
            "type": "chamfer",
            "body": {"$mitcad_bind": "body"},
            "edges": {"$mitcad_bind": "edges"},
            "size": {
                "type": "equal_distance",
                "distance": command_value(node.distance),
            },
        }

    commands = [
        *_parameter_commands(model),
        *base_commands,
    ]
    replay = [
        {
            "bind_single_body": "body",
            "bind_face_boundary_edges": boundary,
            "commands": [
                {
                    "cmd": "add_feature",
                    "name": name,
                    "def": chamfer_def,
                }
            ],
        }
    ]
    dependencies = _native_dependencies((commands, replay))
    return {
        "format": FORMAT,
        "version": VERSION,
        "backend": "mitcad",
        "commands": _plain_command_value(commands),
        "replay": _plain_command_value(replay),
    }, dependencies


def _translated_body_ir(node, offset):
    """Materialize TranslationIR into Mitcad's existing typed CSG placements."""
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
        "Mitcad TranslationIR supports primitive/Boolean CSG bodies only"
    )


def _materialize_translations(node):
    """Remove semantic TranslationIR wrappers only for native lowering."""
    if isinstance(node, TranslationIR):
        return _translated_body_ir(
            _materialize_translations(node.body),
            node.offset,
        )
    if isinstance(node, BooleanIR):
        return BooleanIR(
            operation=node.operation,
            target=_materialize_translations(node.target),
            tool=_materialize_translations(node.tool),
        )
    return node


def _contains_translation(node) -> bool:
    if isinstance(node, TranslationIR):
        return True
    if isinstance(node, BooleanIR):
        return (
            _contains_translation(node.target)
            or _contains_translation(node.tool)
        )
    return False
