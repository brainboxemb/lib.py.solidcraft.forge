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
    BooleanSubtractIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CylinderIR,
    ExtrudeIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    RegionIR,
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


def _box_command(node: PlacementIR, name: str) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, BoxIR):
        raise TypeError("Mitcad box lowering requires PlacementIR(BoxIR)")

    _require_positive(primitive.length, "box length")
    _require_positive(primitive.width, "box width")
    _require_positive(primitive.height, "box height")
    _require_origin_plane(node.point[2], label="Box")

    if node.anchor not in ((0, 0, -1), (0, 0, 0)):
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
        "symmetric": node.anchor == (0, 0, 0),
        "operation": "new_body",
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


def _extrude_commands(
    node: ExtrudeIR,
    name: str,
) -> list[dict]:
    """Lower semantic Sketch/Profile + Extrude IR to native Mitcad features."""
    sketch = node.sketch
    if sketch.plane not in ("XY", "XZ", "YZ"):
        raise ModelError("Mitcad Sketch IR requires XY, XZ or YZ")
    if len(sketch.profiles) != 1 or len(node.regions) != 1:
        raise ModelError(
            "Mitcad Extrude IR currently requires one circle region"
        )

    profile = sketch.profiles[0]
    region = node.regions[0]
    if not isinstance(profile, CircleProfileIR):
        raise ModelError(
            "Mitcad Extrude IR currently requires CircleProfileIR"
        )
    if not isinstance(region, RegionIR) or region.outer != 0 or region.holes:
        raise ModelError(
            "Mitcad Extrude IR currently requires one region without holes"
        )
    if any(parameters_in(value) or pv(value) != 0 for value in profile.center):
        raise ModelError(
            "Mitcad CircleProfileIR currently requires origin center"
        )
    if node.direction not in ("positive", "negative"):
        raise ModelError(
            "Mitcad Extrude IR requires positive or negative direction"
        )

    _require_positive(profile.diameter, "circle diameter")
    _require_positive(node.distance, "sketch extrusion distance")

    radius = pv(profile.diameter) / 2.0
    extent_distance = command_value(
        -node.distance if node.direction == "negative" else node.distance
    )
    center = [command_value(value) for value in profile.center]

    sketch_definition = {
        "type": "sketch",
        "plane": sketch.plane.lower(),
        "entities": [
            {
                "id": "p1",
                "type": "point",
                "at": center,
                "fixed": True,
            },
            {
                "id": "c2",
                "type": "circle",
                "center": "p1",
                "radius": radius,
            },
        ],
        "constraints": [],
        "dimensions": [
            {
                "id": "k1",
                "type": "diameter",
                "curve": "c2",
                "value": command_value(profile.diameter),
            }
        ],
    }
    extrude_definition = {
        "type": "extrude",
        "profiles": [
            {
                "sketch": {"ref": "sk.uid"},
                "point": center,
            }
        ],
        "extent": {
            "type": "distance",
            "distance": extent_distance,
        },
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
    if len(node.edges.faces) != 1:
        raise ModelError(
            "Mitcad face-boundary chamfer currently requires one Faces value"
        )

    face = node.edges.faces[0]
    try:
        normal = _FACE_NORMALS[face]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad backend does not support Forge face {face!r}"
        ) from exc

    commands = [
        *_parameter_commands(model),
        _box_command(node.base, f"{name}Base"),
    ]
    replay = [
        {
            "bind_single_body": "body",
            "bind_face_boundary_edges": {
                "name": "edges",
                "body": "body",
                "face": {
                    "surface": "plane",
                    "normal": normal,
                    "normal_tolerance": 1e-6,
                },
            },
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
        else:
            raise ModelError(
                f"Mitcad backend does not support placed Forge IR primitive "
                f"{type(node.primitive).__name__!r}"
            )
    elif isinstance(node, ExtrudeIR):
        geometry_commands = _extrude_commands(node, name)
    elif isinstance(node, BooleanSubtractIR):
        geometry_commands = [
            _box_command(node.target, f"{name}Base"),
            _cylinder_command(
                node.tool,
                f"{name}Cut",
                operation="cut",
            ),
        ]
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
