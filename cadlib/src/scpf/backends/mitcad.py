"""Lower typed Forge semantic IR to native Mitcad commands.

Mitcad never interprets raw Shape.data. Unsupported Forge semantics arrive as
LegacyShapeIR and fail explicitly until they receive a typed IR node and a
qualified native lowering.
"""
from __future__ import annotations

from ..compiler import ModelError, _require_positive
from ..core import (
    Shape,
    _DirectionSelector,
    _box_corner_from_anchor,
    _native_dependencies,
    _plain_command_value,
    _pv as pv,
    command_value,
    parameters_in,
)
from ..ir import (
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CylinderIR,
    ExtrudeIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PolygonProfileIR,
    RegionIR,
    SphereIR,
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
    """Publish Forge model parameters as native Mitcad user parameters."""
    return [
        {
            "cmd": "add_parameter",
            "name": parameter.name,
            "value": parameter.value,
            "unit": parameter.unit,
        }
        for parameter in model.parameters
    ]


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


def _extrude_commands(
    node: ExtrudeIR,
    name: str,
) -> list[dict]:
    """Lower semantic Sketch/Profile + Extrude IR to native Mitcad features."""
    sketch = node.sketch
    if sketch.plane not in ("XY", "XZ", "YZ"):
        raise ModelError("Mitcad Sketch IR requires XY, XZ or YZ")
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
        "plane": sketch.plane.lower(),
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
