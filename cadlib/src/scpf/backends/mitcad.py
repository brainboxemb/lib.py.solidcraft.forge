"""Lower typed Forge semantic IR to native Mitcad commands.

Mitcad never interprets raw Shape.data. Unsupported Forge semantics arrive as
LegacyShapeIR and fail explicitly until they receive a typed IR node and a
qualified native lowering.
"""
from __future__ import annotations

from math import isfinite

from ..compiler import ModelError, _require_positive
from ..core import (
    Shape,
    _DirectionSelector,
    _box_corner_from_anchor,
    _native_dependencies,
    _plain_command_value,
    _pv as pv,
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
    CylinderIR,
    ExtrudeIR,
    FeatureRefIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    SphereIR,
    SuppressionColumnIR,
    _region_interior_point,
    normalize_shape,
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
        if parameter.unit == "deg":
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


def _sphere_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, SphereIR):
        raise TypeError("Mitcad sphere lowering requires PlacementIR(SphereIR)")
    _require_positive(primitive.radius, "sphere radius")
    if node.anchor != (0, 0, 0):
        raise ModelError("Mitcad Sphere IR currently requires Anchor.CENTER")
    _require_origin_plane(node.point[2], label="Sphere")
    return {
        "cmd": "add_feature",
        "name": name,
        "def": {
            "type": "sphere",
            "plane": "xy",
            "center": [
                command_value(node.point[0]),
                command_value(node.point[1]),
            ],
            "diameter": command_value(primitive.radius * 2),
            "operation": operation,
            "participants": [],
        },
    }


def _csg_primitive_command(
    node: PlacementIR,
    name: str,
    operation: str,
) -> dict:
    if isinstance(node.primitive, BoxIR):
        return _box_command(node, name, operation=operation)
    if isinstance(node.primitive, CylinderIR):
        return _cylinder_command(node, name, operation=operation)
    if isinstance(node.primitive, SphereIR):
        return _sphere_command(node, name, operation=operation)
    raise ModelError(
        "Mitcad primitive CSG does not support "
        f"{type(node.primitive).__name__}"
    )


def _boolean_commands(node: BooleanIR, name: str) -> list[dict]:
    """Flatten one bounded left-associated semantic CSG tree in source order."""
    commands = []
    if isinstance(node.target, BooleanIR):
        commands.extend(_boolean_commands(node.target, name))
    elif isinstance(node.target, PlacementIR):
        commands.append(
            _csg_primitive_command(node.target, f"{name}Base", "new_body")
        )
    else:
        raise ModelError("Mitcad BooleanIR has unsupported target")

    commands.append(
        _csg_primitive_command(
            node.tool,
            f"{name}{node.operation.title()}{len(commands)}",
            node.operation,
        )
    )
    return commands


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


def _mitcad_sketch_plane(plane: PlaneIR):
    """Lower PlaneIR; construction-plane identity stays backend transport."""
    offset = _principal_plane_offset(
        plane,
        label="Mitcad Sketch IR",
    )
    if not parameters_in(offset) and abs(pv(offset)) <= 1e-12:
        return [], plane.orientation.lower()

    return [
        {
            "cmd": "add_feature",
            "as": "plane",
            "def": {
                "type": "construction_plane",
                "definition": {
                    "type": "offset",
                    "plane": plane.orientation.lower(),
                    "distance": command_value(offset),
                },
            },
        }
    ], {"ref": "plane.uid"}


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
        if any(
            parameters_in(value)
            for point in profile.points
            for value in point
        ):
            raise ModelError(
                "Mitcad PolygonProfileIR currently requires fixed coordinates"
            )

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

        selector = center if not region.holes else [pick[0], pick[1]]
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
        "constraints": [],
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


def _parameterized_rectangle_sketch(profile: PolygonProfileIR):
    """Return native Mitcad sketch relations for the #381 rectangle slice."""
    if len(profile.points) != 4:
        raise ModelError(
            "Mitcad parameterized RevolveIR currently requires a rectangle"
        )

    p1, p2, p3, p4 = profile.points
    values = tuple(
        tuple(float(pv(value)) for value in point)
        for point in profile.points
    )
    if any(
        parameters_in(value)
        for value in (p1[0], p1[1], p2[0], p4[1])
    ):
        raise ModelError(
            "Mitcad parameterized RevolveIR rectangle must start at origin"
        )
    if (
        abs(values[0][0]) > 1e-12
        or abs(values[0][1]) > 1e-12
        or abs(values[1][0]) > 1e-12
        or abs(values[3][1]) > 1e-12
        or not _same_semantic_value(p2[1], p3[1])
        or not _same_semantic_value(p3[0], p4[0])
        or values[1][1] <= 0
        or values[2][0] <= 0
    ):
        raise ModelError(
            "Mitcad parameterized RevolveIR currently requires an "
            "origin-based axis-aligned rectangle"
        )

    entities = [
        {"id": "p1", "type": "point", "at": list(values[0]), "fixed": True},
        {"id": "p2", "type": "point", "at": list(values[1])},
        {"id": "p3", "type": "point", "at": list(values[2])},
        {"id": "p4", "type": "point", "at": list(values[3])},
        {"id": "c5", "type": "line", "start": "p1", "end": "p2"},
        {"id": "c6", "type": "line", "start": "p2", "end": "p3"},
        {"id": "c7", "type": "line", "start": "p3", "end": "p4"},
        {"id": "c8", "type": "line", "start": "p4", "end": "p1"},
    ]
    constraints = [
        {"id": "k9", "type": "vertical", "line": "c5"},
        {"id": "k10", "type": "horizontal", "line": "c6"},
        {"id": "k11", "type": "vertical", "line": "c7"},
        {"id": "k12", "type": "horizontal", "line": "c8"},
    ]
    dimensions = [
        {"id": "k13", "type": "length", "line": "c5",
         "value": command_value(p2[1])},
        {"id": "k14", "type": "length", "line": "c6",
         "value": command_value(p3[0])},
    ]
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
    if parameterized:
        entities, constraints, dimensions = _parameterized_rectangle_sketch(profile)
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
        extent = {"type": "angle", "angle": command_value(node.angle)}
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
        or configuration.columns[0].feature != FeatureRefIR(("root",))
    ):
        raise ModelError(
            "Mitcad ConfigurationIR currently requires one root suppression column"
        )
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



def _chamfer_document(
    model: ModelIR,
    node: ChamferIR,
    name: str,
):
    _require_positive(node.distance, "chamfer distance")
    if not node.edges.faces:
        raise ModelError("Mitcad face-boundary chamfer has no Faces values")

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
                    "def": {
                        "type": "chamfer",
                        "body": {"$mitcad_bind": "body"},
                        "edges": {"$mitcad_bind": "edges"},
                        "size": {
                            "type": "equal_distance",
                            "distance": command_value(node.distance),
                        },
                    },
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
    if isinstance(node, RevolveIR) and node.operation == "cut":
        return _revolve_cut_document(model, node, name)

    if isinstance(node, PlacementIR):
        if isinstance(node.primitive, BoxIR):
            geometry_commands = [_box_command(node, name)]
        elif isinstance(node.primitive, CylinderIR):
            geometry_commands = [_cylinder_command(node, name)]
        elif isinstance(node.primitive, SphereIR):
            geometry_commands = [_sphere_command(node, name)]
        else:
            raise ModelError(
                f"Mitcad backend does not support placed Forge IR primitive "
                f"{type(node.primitive).__name__!r}"
            )
    elif isinstance(node, ExtrudeIR):
        geometry_commands = _extrude_commands(node, name)
    elif isinstance(node, RevolveIR):
        geometry_commands = _revolve_commands(node, name)
    elif isinstance(node, BooleanIR):
        geometry_commands = _boolean_commands(node, name)
    else:
        raise ModelError(
            f"Mitcad backend does not support Forge IR node "
            f"{type(node).__name__!r}"
        )

    commands = [
        *_parameter_commands(model),
        *geometry_commands,
    ]
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
