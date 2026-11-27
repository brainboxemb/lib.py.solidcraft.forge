"""Lower typed Forge semantic IR to native Mitcad commands.

Mitcad never interprets raw Shape.data. Unsupported Forge semantics arrive as
LegacyShapeIR and fail explicitly until they receive a typed IR node and a
qualified native lowering.
"""
from __future__ import annotations

from math import isfinite

from ..compiler import ModelError, _require_positive
from ..core import (
    Expression,
    Parameter,
    Shape,
    _DirectionSelector,
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
from ..ir import (
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
    _region_interior_point,
    normalize_shape,
    resolve_feature_ref,
)
from ..scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
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


def _parameter_commands(model: ModelIR) -> list[dict]:
    """Publish Forge model parameters with native Mitcad unit semantics."""
    commands = []
    for parameter in model.parameters:
        command = {
            "cmd": "add_parameter",
            "name": parameter.name,
            "unit": parameter.unit,
        }
        if len(parameter.roles) > 1:
            # One Forge source parameter may feed multiple physical roles.
            # Keep one editable native Number and add units at typed use sites.
            command["expression"] = number_text(parameter.value)
        elif parameter.unit == "deg":
            # Mitcad JSON numbers in angular slots are radians even when the
            # display unit is degrees. A unit-bearing expression preserves
            # Forge's authored degree value and remains a native parameter.
            command["expression"] = (
                f"{number_text(parameter.value)} deg"
            )
        else:
            command["value"] = parameter.value
        commands.append(command)
    return commands


def _role_scalar_expression_text(
    model: ModelIR,
    node,
    role: str,
    *,
    scalar_literal: bool = False,
) -> str:
    """Render bounded semantic scalar IR for one typed Mitcad use site."""
    unit = "mm" if role == "length" else "deg"
    parameters = {parameter.name: parameter for parameter in model.parameters}

    if isinstance(node, ScalarLiteralIR):
        text = number_text(node.value)
        return text if scalar_literal else f"{text} {unit}"

    if isinstance(node, ScalarParameterRefIR):
        parameter = parameters.get(node.name)
        if parameter is None:
            raise ModelError(
                f"semantic scalar expression references unknown parameter {node.name!r}"
            )
        if role not in parameter.roles:
            raise ModelError(
                f"parameter {node.name!r} has no semantic {role} role"
            )
        if len(parameter.roles) > 1:
            return f"{node.name} * 1 {unit}"
        return node.name

    if isinstance(node, ScalarUnaryIR):
        if node.operation != "negate":
            raise ModelError(
                f"unsupported scalar unary operation {node.operation!r}"
            )
        return f"-({_role_scalar_expression_text(model, node.operand, role)})"

    if not isinstance(node, ScalarBinaryIR):
        raise ModelError("typed scalar expression has unsupported IR node")

    if node.operation in {"add", "subtract"}:
        operator = "+" if node.operation == "add" else "-"
        return (
            f"({_role_scalar_expression_text(model, node.left, role)}) "
            f"{operator} "
            f"({_role_scalar_expression_text(model, node.right, role)})"
        )

    if node.operation == "multiply":
        if isinstance(node.left, ScalarLiteralIR):
            return (
                f"{_role_scalar_expression_text(model, node.left, role, scalar_literal=True)} "
                f"* ({_role_scalar_expression_text(model, node.right, role)})"
            )
        if isinstance(node.right, ScalarLiteralIR):
            return (
                f"({_role_scalar_expression_text(model, node.left, role)}) * "
                f"{_role_scalar_expression_text(model, node.right, role, scalar_literal=True)}"
            )

    if (
        node.operation == "divide"
        and isinstance(node.right, ScalarLiteralIR)
        and node.right.value != 0
    ):
        return (
            f"({_role_scalar_expression_text(model, node.left, role)}) / "
            f"{_role_scalar_expression_text(model, node.right, role, scalar_literal=True)}"
        )

    raise ModelError(
        "typed scalar expression requires affine numeric scaling"
    )


def _role_command_value(model: ModelIR | None, value, role: str):
    """Spell one typed use of a mixed-role source parameter or expression."""
    if role not in {"length", "angle"}:
        raise ModelError(f"unsupported Forge parameter role {role!r}")
    if model is None:
        return command_value(value)

    mixed_names = {
        parameter.name
        for parameter in model.parameters
        if len(parameter.roles) > 1
    }
    used_mixed = [
        parameter
        for parameter in parameters_in(value)
        if parameter.name in mixed_names
    ]
    if not used_mixed:
        return command_value(value)
    if len(used_mixed) != 1:
        raise ModelError(
            "mixed-role scalar expressions currently require one mixed source parameter"
        )

    if isinstance(value, Parameter):
        node = ScalarParameterRefIR(value.name)
    elif isinstance(value, Expression) and value.scalar_ir is not None:
        node = value.scalar_ir
    else:
        raise ModelError(
            "mixed-role Forge expression has no typed scalar semantics"
        )

    if not is_affine_scalar_expression(node):
        raise ModelError(
            "mixed-role Forge expression is outside affine scalar IR"
        )
    dependencies = scalar_parameter_names(node)
    return _native_expression(
        _role_scalar_expression_text(model, node, role),
        dependencies,
    )


def _require_origin_plane(value, *, label):
    """Refuse axial placement that this Mitcad slice cannot preserve yet."""
    if parameters_in(value) or pv(value) != 0:
        raise ModelError(
            f"Mitcad {label} placement currently requires its axial "
            "coordinate on the origin plane"
        )


def _box_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, BoxIR):
        raise TypeError("Mitcad box lowering requires PlacementIR(BoxIR)")

    _require_positive(primitive.length, "box length")
    _require_positive(primitive.width, "box width")
    height = _require_positive(primitive.height, "box height")

    if node.anchor == (0, 0, -1):
        _require_origin_plane(node.point[2], label="Box")
        symmetric = False
    elif node.anchor == (0, 0, 0):
        axial = pv(node.point[2])
        if parameters_in(node.point[2]):
            raise ModelError(
                "Mitcad Box axial placement currently requires a numeric "
                "origin-plane equivalent"
            )
        if abs(axial) <= 1e-9:
            symmetric = True
        elif not parameters_in(primitive.height) and abs(axial - height / 2.0) <= 1e-9:
            # A centered Forge box whose bottom lies on XY is the same native
            # solid as a one-sided Mitcad box starting on XY.
            symmetric = False
        else:
            raise ModelError(
                "Mitcad Box placement currently requires its center on XY "
                "or its bottom face on XY"
            )
    else:
        raise ModelError(
            "Mitcad Box placement currently supports Anchor.BOTTOM or "
            "Anchor.CENTER only"
        )

    corner = _box_corner_from_anchor(
        primitive.length,
        primitive.width,
        primitive.height,
        node.point,
        _DirectionSelector(node.anchor),
    )

    definition = {
        "type": "box",
        "plane": "xy",
        "corner": [
            command_value(corner[0]),
            command_value(corner[1]),
        ],
        "length": command_value(primitive.length),
        "width": command_value(primitive.width),
        "height": command_value(primitive.height),
        "symmetric": symmetric,
        "operation": operation,
        "participants": [],
    }
    return {
        "cmd": "add_feature",
        "name": name,
        "def": definition,
    }


_CYLINDER_PLANES = {
    "X": ("yz", (-1, 0, 0), 0),
    "Y": ("xz", (0, -1, 0), 1),
    "Z": ("xy", (0, 0, -1), 2),
}


def _cylinder_plane_center(axis, point):
    if axis == "X":
        # Mitcad YZ plane coordinates: u=-Z, v=+Y.
        return (-point[2], point[1])
    if axis == "Y":
        # Mitcad XZ plane coordinates: u=+X, v=-Z.
        return (point[0], -point[2])
    if axis == "Z":
        return (point[0], point[1])
    raise ModelError(
        f"Mitcad Cylinder IR requires a principal axis, got {axis!r}"
    )


def _cylinder_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, CylinderIR):
        raise TypeError(
            "Mitcad cylinder lowering requires PlacementIR(CylinderIR)"
        )

    _require_positive(primitive.height, "cylinder height")
    _require_positive(primitive.diameter, "cylinder diameter")
    try:
        plane, axial_start, axial_index = _CYLINDER_PLANES[primitive.axis]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad Cylinder IR requires a principal axis, "
            f"got {primitive.axis!r}"
        ) from exc

    _require_origin_plane(
        node.point[axial_index],
        label="Cylinder",
    )
    if node.anchor not in ((0, 0, 0), axial_start):
        raise ModelError(
            "Mitcad Cylinder placement currently supports CENTER or the "
            "negative axial end anchor only"
        )

    center = _cylinder_plane_center(primitive.axis, node.point)
    return {
        "cmd": "add_feature",
        "name": name,
        "def": {
            "type": "cylinder",
            "plane": plane,
            "center": [
                command_value(center[0]),
                command_value(center[1]),
            ],
            "diameter": command_value(primitive.diameter),
            "height": command_value(primitive.height),
            "symmetric": node.anchor == (0, 0, 0),
            "operation": operation,
            "participants": [],
        },
    }


def _cone_commands(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
    plane_binding: str = "cone_plane",
) -> list[dict]:
    """Lower semantic Cone placement through a principal support plane."""
    primitive = node.primitive
    if not isinstance(primitive, ConeIR):
        raise TypeError("Mitcad cone lowering requires PlacementIR(ConeIR)")

    _require_positive(primitive.height, "cone height")
    _require_positive(primitive.diameter, "cone diameter")
    if pv(primitive.top_diameter) < 0:
        raise ModelError("cone top diameter must be zero or positive")

    try:
        plane, _axial_start, axial_index = _CYLINDER_PLANES[primitive.axis]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad ConeIR requires a principal axis, got {primitive.axis!r}"
        ) from exc

    selector = _DirectionSelector(node.anchor)
    try:
        base = _cone_base_from_anchor(
            primitive.height,
            primitive.axis,
            node.point,
            selector,
        )
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    plane_commands, native_plane = _mitcad_offset_plane(
        plane.upper(),
        base[axial_index],
        label="Cone",
        binding=plane_binding,
    )
    center = _cylinder_plane_center(primitive.axis, base)

    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "name": name,
            "def": {
                "type": "cone",
                "plane": native_plane,
                "center": [
                    command_value(center[0]),
                    command_value(center[1]),
                ],
                "radius": command_value(primitive.diameter / 2),
                "top_radius": command_value(primitive.top_diameter / 2),
                "height": command_value(primitive.height),
                "symmetric": False,
                "operation": operation,
                "participants": [],
            },
        },
    ]


def _sphere_center(node: PlacementIR):
    """Derive semantic Sphere centre from PlacementIR before native transport."""
    primitive = node.primitive
    if not isinstance(primitive, SphereIR):
        raise TypeError("Mitcad sphere lowering requires PlacementIR(SphereIR)")
    _require_positive(primitive.radius, "sphere radius")
    return _sphere_center_from_anchor(
        primitive.radius,
        node.point,
        _DirectionSelector(node.anchor),
    )


def _sphere_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    """Lower the already-qualified origin-plane Sphere CSG spelling."""
    primitive = node.primitive
    center = _sphere_center(node)
    _require_origin_plane(center[2], label="Sphere CSG")
    return {
        "cmd": "add_feature",
        "name": name,
        "def": {
            "type": "sphere",
            "plane": "xy",
            "center": [
                command_value(center[0]),
                command_value(center[1]),
            ],
            "diameter": command_value(primitive.radius * 2),
            "operation": operation,
            "participants": [],
        },
    }


def _sphere_commands(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
    plane_binding: str = "sphere_plane",
) -> list[dict]:
    """Lower Sphere placement with backend-owned support geometry."""
    primitive = node.primitive
    center = _sphere_center(node)
    plane_commands, native_plane = _mitcad_offset_plane(
        "XY",
        center[2],
        label="Sphere",
        binding=plane_binding,
    )
    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "name": name,
            "def": {
                "type": "sphere",
                "plane": native_plane,
                "center": [
                    command_value(center[0]),
                    command_value(center[1]),
                ],
                "diameter": command_value(primitive.radius * 2),
                "operation": operation,
                "participants": [],
            },
        },
    ]


def _csg_helper_binding(path: tuple[str, ...]) -> str:
    """Return one deterministic backend-private binding for semantic CSG path."""
    return "csg_plane_" + "_".join(path)


def _csg_primitive_commands(
    node: PlacementIR,
    name: str,
    operation: str,
    *,
    path: tuple[str, ...],
) -> tuple[list[dict], int]:
    """Lower one semantic primitive to native helpers + one feature command.

    The returned index is relative to this command group and identifies the
    native command representing the semantic Forge feature. Private helper
    commands before it are never semantic history entries.
    """
    if isinstance(node.primitive, BoxIR):
        return [_box_command(node, name, operation=operation)], 0
    if isinstance(node.primitive, CylinderIR):
        return [_cylinder_command(node, name, operation=operation)], 0
    if isinstance(node.primitive, ConeIR):
        commands = _cone_commands(
            node,
            name,
            operation=operation,
            plane_binding=_csg_helper_binding(path),
        )
        return commands, len(commands) - 1
    if isinstance(node.primitive, SphereIR):
        commands = _sphere_commands(
            node,
            name,
            operation=operation,
            plane_binding=_csg_helper_binding(path),
        )
        return commands, len(commands) - 1
    raise ModelError(
        "Mitcad primitive CSG does not support "
        f"{type(node.primitive).__name__}"
    )


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


def _mitcad_offset_plane(
    orientation: str,
    offset,
    *,
    label: str,
    binding: str = "plane",
):
    """Lower one principal offset plane; native identity stays transport only."""
    if orientation not in ("XY", "XZ", "YZ"):
        raise ModelError(f"Mitcad {label} requires a principal plane")
    if not parameters_in(offset) and abs(pv(offset)) <= 1e-12:
        return [], orientation.lower()

    return [
        {
            "cmd": "add_feature",
            "as": binding,
            "def": {
                "type": "construction_plane",
                "definition": {
                    "type": "offset",
                    "plane": orientation.lower(),
                    "distance": command_value(offset),
                },
            },
        }
    ], {"ref": f"{binding}.uid"}


def _mitcad_sketch_plane(plane: PlaneIR):
    """Lower PlaneIR through the shared principal-plane transport."""
    offset = _principal_plane_offset(
        plane,
        label="Mitcad Sketch IR",
    )
    return _mitcad_offset_plane(
        plane.orientation,
        offset,
        label="Sketch IR",
    )


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


def _same_semantic_value(left, right) -> bool:
    """Compare authored scalar intent without using current values as identity."""
    return str(command_value(left)) == str(command_value(right))


def _sketch_relations_transport(
    relations: SketchRelationsIR,
    model: ModelIR | None = None,
):
    """Lower explicit semantic Sketch relations to Mitcad-native solver data."""
    if not isinstance(relations, SketchRelationsIR):
        raise ModelError("Mitcad Sketch relations require SketchRelationsIR")

    coordinate_mode = bool(relations.coordinate_dimensions)
    entities = []
    point_ids = []

    if coordinate_mode:
        # A fixed origin entity is native solver transport. Semantic coordinate
        # dimensions reference the Sketch origin, not this Mitcad uid.
        entities.append(
            {
                "id": "p1",
                "type": "point",
                "at": [0.0, 0.0],
                "fixed": True,
            }
        )
        point_start = 2
    else:
        point_start = 1

    for index, point in enumerate(relations.points, start=point_start):
        point_id = f"p{index}"
        point_ids.append(point_id)
        at = [float(pv(value)) for value in point.position]
        if any(not isfinite(value) for value in at):
            raise ModelError("Mitcad Sketch relation points require finite seed values")
        entity = {
            "id": point_id,
            "type": "point",
            "at": at,
        }
        if not coordinate_mode and index == 1:
            # Solver anchoring for the #440 rectangle remains backend transport.
            if any(
                parameters_in(value) or abs(pv(value)) > 1e-12
                for value in point.position
            ):
                raise ModelError(
                    "Mitcad #440 Sketch relations require the first semantic point at origin"
                )
            entity["fixed"] = True
        entities.append(entity)

    first_curve = point_start + len(point_ids)
    curve_ids = []
    for offset, line in enumerate(relations.lines):
        curve_id = f"c{first_curve + offset}"
        curve_ids.append(curve_id)
        entities.append(
            {
                "id": curve_id,
                "type": "line",
                "start": point_ids[line.start],
                "end": point_ids[line.end],
            }
        )

    first_relation = first_curve + len(curve_ids)
    constraints = [
        {
            "id": f"k{first_relation + offset}",
            "type": constraint.orientation,
            "line": curve_ids[constraint.line],
        }
        for offset, constraint in enumerate(relations.constraints)
    ]
    first_dimension = first_relation + len(constraints)
    dimensions = [
        {
            "id": f"k{first_dimension + offset}",
            "type": "length",
            "line": curve_ids[dimension.line],
            "value": _role_command_value(model, dimension.value, "length"),
        }
        for offset, dimension in enumerate(relations.dimensions)
    ]

    coordinate_start = first_dimension + len(dimensions)
    for offset, dimension in enumerate(relations.coordinate_dimensions):
        dimensions.append(
            {
                "id": f"k{coordinate_start + offset}",
                "type": (
                    "horizontal_distance"
                    if dimension.axis == "x"
                    else "vertical_distance"
                ),
                "a": "p1",
                "b": point_ids[dimension.point],
                "signed": True,
                "value": _role_command_value(model, dimension.value, "length"),
            }
        )

    return entities, constraints, dimensions


def _next_sketch_entity_number(entities: list[dict]) -> int:
    numbers = []
    for entity in entities:
        uid = entity.get("id")
        if (
            isinstance(uid, str)
            and len(uid) > 1
            and uid[0] in {"p", "c", "t"}
            and uid[1:].isdigit()
        ):
            numbers.append(int(uid[1:]))
    return max(numbers, default=0) + 1


def _next_sketch_relation_number(
    constraints: list[dict],
    dimensions: list[dict],
) -> int:
    numbers = []
    for relation in (*constraints, *dimensions):
        uid = relation.get("id")
        if (
            isinstance(uid, str)
            and uid.startswith("k")
            and uid[1:].isdigit()
        ):
            numbers.append(int(uid[1:]))
    return max(numbers, default=0) + 1


def _shifted_xy_axis_transport(
    axis: AxisLineIR,
    plane: PlaneIR,
    entities: list[dict],
    constraints: list[dict],
    dimensions: list[dict],
) -> dict:
    """Append Mitcad-only construction geometry for one shifted XY axis."""
    if axis.direction not in {"X", "Y"}:
        raise ModelError(
            "Mitcad shifted AxisLineIR on XY requires X or Y direction"
        )
    if (
        plane.orientation != "XY"
        or not _same_semantic_value(axis.origin[2], plane.origin[2])
    ):
        raise ModelError(
            "Mitcad shifted AxisLineIR must lie in the semantic XY PlaneIR"
        )

    next_entity = _next_sketch_entity_number(entities)
    origin_id = f"p{next_entity}"
    first_id = f"p{next_entity + 1}"
    second_id = f"p{next_entity + 2}"
    curve_id = f"c{next_entity + 3}"

    entities.append(
        {
            "id": origin_id,
            "type": "point",
            "at": [0.0, 0.0],
            "fixed": True,
        }
    )

    if axis.direction == "Y":
        offset = axis.origin[0]
        offset_value = float(pv(offset))
        first = [offset_value, -1.0]
        second = [offset_value, 1.0]
        orientation = "vertical"
        offset_dimension = "horizontal_distance"
        along_dimension = "vertical_distance"
    else:
        offset = axis.origin[1]
        offset_value = float(pv(offset))
        first = [-1.0, offset_value]
        second = [1.0, offset_value]
        orientation = "horizontal"
        offset_dimension = "vertical_distance"
        along_dimension = "horizontal_distance"

    entities.extend(
        [
            {"id": first_id, "type": "point", "at": first},
            {"id": second_id, "type": "point", "at": second},
            {
                "id": curve_id,
                "type": "line",
                "start": first_id,
                "end": second_id,
                "construction": True,
            },
        ]
    )

    next_relation = _next_sketch_relation_number(
        constraints,
        dimensions,
    )
    constraints.append(
        {
            "id": f"k{next_relation}",
            "type": orientation,
            "line": curve_id,
        }
    )
    dimensions.extend(
        [
            {
                "id": f"k{next_relation + 1}",
                "type": offset_dimension,
                "a": origin_id,
                "b": first_id,
                "signed": True,
                "value": command_value(offset),
            },
            {
                "id": f"k{next_relation + 2}",
                "type": along_dimension,
                "a": origin_id,
                "b": first_id,
                "signed": True,
                "value": -1.0,
            },
            {
                "id": f"k{next_relation + 3}",
                "type": along_dimension,
                "a": origin_id,
                "b": second_id,
                "signed": True,
                "value": 1.0,
            },
        ]
    )

    return {
        "sketch": {"ref": "sk.uid"},
        "curve": curve_id,
    }


def _mitcad_revolve_axis(
    node: RevolveIR,
    entities: list[dict],
    constraints: list[dict],
    dimensions: list[dict],
):
    axis = node.axis
    if not isinstance(axis, AxisLineIR):
        raise ModelError("Mitcad RevolveIR requires AxisLineIR")

    if all(
        not parameters_in(value) and abs(pv(value)) <= 1e-12
        for value in axis.origin
    ):
        return axis.direction.lower()

    if node.sketch.plane.orientation != "XY":
        raise ModelError(
            "Mitcad shifted AxisLineIR transport currently requires an XY Sketch"
        )
    return _shifted_xy_axis_transport(
        axis,
        node.sketch.plane,
        entities,
        constraints,
        dimensions,
    )


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


def _private_suppression_parameter(model: ModelIR) -> str:
    """Choose one backend-private driver outside semantic model parameters."""
    taken = {parameter.name for parameter in model.parameters}
    stem = "__forge_suppress_root"
    if stem not in taken:
        return stem
    index = 2
    while f"{stem}_{index}" in taken:
        index += 1
    return f"{stem}_{index}"


def _mitcad_configuration_commands(
    model: ModelIR,
    configuration: ConfigurationIR,
    *,
    feature_binding: str,
) -> list[dict]:
    """Lower suppression-only semantic configuration to native Mitcad state."""
    if (
        len(configuration.columns) != 1
        or not isinstance(configuration.columns[0], SuppressionColumnIR)
    ):
        raise ModelError(
            "Mitcad ConfigurationIR currently requires one suppression column"
        )
    resolve_feature_ref(model.root, configuration.columns[0].feature)
    if any(len(row.cells) != 1 for row in configuration.rows):
        raise ModelError(
            "Mitcad ConfigurationIR currently requires one suppression cell per row"
        )

    driver = _private_suppression_parameter(model)
    return [
        {
            "cmd": "add_parameter",
            "name": driver,
            "unit": "",
            "expression": "0",
        },
        {
            "cmd": "set_configurations",
            "configurations": {
                "options": [],
                "closed": True,
                "parameters": [driver],
                "default": configuration.active,
                "rows": [
                    {
                        "name": row.name,
                        "values": {
                            driver: "1" if row.cells[0] else "0",
                        },
                    }
                    for row in configuration.rows
                ],
            },
        },
        {
            "cmd": "suppress_feature",
            "uid": {"ref": f"{feature_binding}.uid"},
            "expression": f"{driver} > 0",
        },
        {
            "cmd": "apply_configuration",
            "name": configuration.active,
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

def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Compile the qualified Forge semantic IR subset to Mitcad intent."""
    if not isinstance(model, ModelIR):
        raise TypeError("Mitcad backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    node = model.root
    if isinstance(node, LegacyShapeIR):
        raise ModelError(
            "Mitcad backend does not yet support Forge shape kind "
            f"{node.source_kind!r}; no qualified semantic IR lowering exists"
        )

    if isinstance(node, ChamferIR):
        return _chamfer_document(model, node, name)
    if isinstance(node, FilletIR):
        return _fillet_document(model, node, name)
    if (
        isinstance(node, BooleanIR)
        and isinstance(node.target, FilletIR)
    ):
        if (
            node.operation != "join"
            or not isinstance(node.tool, PlacementIR)
            or not isinstance(node.tool.primitive, ConeIR)
        ):
            raise ModelError(
                "Mitcad FilletIR Boolean composition currently requires Cone join"
            )
        return _fillet_document(
            model,
            node.target,
            name,
            tool=node.tool,
        )
    if isinstance(node, RevolveIR) and node.operation == "cut":
        return _revolve_cut_document(model, node, name)

    if isinstance(node, PlacementIR):
        if isinstance(node.primitive, BoxIR):
            geometry_commands = [_box_command(node, name)]
        elif isinstance(node.primitive, CylinderIR):
            geometry_commands = [_cylinder_command(node, name)]
        elif isinstance(node.primitive, ConeIR):
            geometry_commands = _cone_commands(node, name)
        elif isinstance(node.primitive, SphereIR):
            geometry_commands = _sphere_commands(node, name)
        else:
            raise ModelError(
                f"Mitcad backend does not support placed Forge IR primitive "
                f"{type(node.primitive).__name__!r}"
            )
    elif isinstance(node, ExtrudeIR):
        geometry_commands = _extrude_commands(node, name)
    elif isinstance(node, RevolveIR):
        geometry_commands = _revolve_commands(model, node, name)
    elif isinstance(node, BooleanIR):
        geometry_commands, feature_indexes = _boolean_command_plan(node, name)
        if model.configuration is not None:
            reference = model.configuration.columns[0].feature
            resolve_feature_ref(node, reference)
            try:
                selected = feature_indexes[reference.path]
            except KeyError as exc:
                raise ModelError(
                    f"Mitcad semantic feature path {reference.path!r} "
                    "has no native feature"
                ) from exc
            command = dict(geometry_commands[selected])
            command["as"] = "configured_feature"
            geometry_commands[selected] = command
    else:
        raise ModelError(
            f"Mitcad backend does not support Forge IR node "
            f"{type(node).__name__!r}"
        )

    commands = [
        *_parameter_commands(model),
        *geometry_commands,
    ]
    if model.configuration is not None:
        if not isinstance(node, BooleanIR):
            raise ModelError(
                "Mitcad configured non-Revolve geometry is outside the qualified history slice"
            )
        commands.extend(
            _mitcad_configuration_commands(
                model,
                model.configuration,
                feature_binding="configured_feature",
            )
        )
    dependencies = _native_dependencies(commands)
    return {
        "format": FORMAT,
        "version": VERSION,
        "backend": "mitcad",
        "commands": _plain_command_value(commands),
    }, dependencies


def compile_ir(model: ModelIR, name: str) -> dict:
    return compile_ir_with_dependencies(model, name)[0]


def compile_model_with_dependencies(shape: Shape, name: str):
    """Compatibility wrapper: normalize Shape before Mitcad lowering."""
    return compile_ir_with_dependencies(normalize_shape(shape), name)


def compile_model(shape: Shape, name: str) -> dict:
    """Compile one Forge Shape through semantic IR to Mitcad commands."""
    return compile_model_with_dependencies(shape, name)[0]


__all__ = [
    "FORMAT",
    "VERSION",
    "compile_ir",
    "compile_ir_with_dependencies",
    "compile_model",
    "compile_model_with_dependencies",
]
