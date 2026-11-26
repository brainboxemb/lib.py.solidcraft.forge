"""Lower typed Forge semantic IR to native SolidCraft commands.

Portable IR nodes are lowered directly here. LegacyShapeIR is the explicit
transition boundary for stable Forge functionality that has not yet migrated
to typed semantic IR.
"""
from __future__ import annotations

from math import isfinite

from ..compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from ..core import (
    Expression,
    Parameter,
    _DirectionSelector,
    _box_corner_from_anchor,
    _cylinder_base_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    command_value,
    number_text,
)
from ..ir import (
    BooleanSubtractIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CylinderIR,
    ExtrudeIR,
    FaceBoundaryIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    RegionIR,
    _circle_region_interior_point,
)
from ..replay import replay_document


_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}


def _require_positive(value, label):
    number = pv(value)
    if not isfinite(number) or number <= 0:
        raise ModelError(f"{label} must be positive")
    return number


def _command(command_name, **params):
    return {"command": command_name, "params": params}


def _parameter_commands(model: ModelIR) -> list[dict]:
    return [
        _command(
            "parameters.add",
            name=parameter.name,
            expression=number_text(parameter.value),
            unit=parameter.unit,
        )
        for parameter in model.parameters
    ]


def _negative_half(value):
    """Match the accepted SolidCraft symbolic half-expression spelling."""
    if isinstance(value, Parameter):
        return _native_expression(
            f"-{value.name} / 2",
            (value.name,),
        )
    if isinstance(value, Expression):
        expression = command_value(value)
        return _native_expression(
            f"-({expression}) / 2",
            expression.parameters,
        )
    return -pv(value) / 2


def _negative_value(value):
    if isinstance(value, Parameter):
        return _native_expression(f"-{value.name}", (value.name,))
    if isinstance(value, Expression):
        expression = command_value(value)
        return _native_expression(
            f"-({expression})",
            expression.parameters,
        )
    return -pv(value)


def _origin_box_corner(primitive: BoxIR, anchor):
    """Keep the already-qualified direct-Box expression spelling unchanged."""
    dimensions = (
        primitive.length,
        primitive.width,
        primitive.height,
    )
    corner = []
    for dimension, side in zip(dimensions, anchor):
        if side < 0:
            corner.append(0)
        elif side > 0:
            corner.append(_negative_value(dimension))
        else:
            corner.append(_negative_half(dimension))
    return corner


def _box_command(node: PlacementIR, name: str) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, BoxIR):
        raise TypeError("SolidCraft box lowering requires PlacementIR(BoxIR)")

    _require_positive(primitive.length, "box length")
    _require_positive(primitive.width, "box width")
    _require_positive(primitive.height, "box height")
    selector = _DirectionSelector(node.anchor)

    params = {
        "length": command_value(primitive.length),
        "width": command_value(primitive.width),
        "height": command_value(primitive.height),
    }
    if not node.explicit and node.anchor == (0, 0, 0):
        params["center"] = [0, 0, 0]
    elif not node.explicit and tuple(node.point) == (0, 0, 0):
        params["corner"] = [
            command_value(value)
            for value in _origin_box_corner(primitive, node.anchor)
        ]
    else:
        corner = _box_corner_from_anchor(
            primitive.length,
            primitive.width,
            primitive.height,
            node.point,
            selector,
        )
        params["corner"] = [
            command_value(value)
            for value in corner
        ]
    params["body_name"] = name
    return _command("solid.box", **params)


def _csg_box_command(node: PlacementIR, name: str) -> dict:
    # Preserve the accepted #246 SolidCraft command shape rather than changing
    # native command spelling merely because placement moved into typed IR.
    command = _box_command(node, name)
    command["params"]["operation"] = "new"
    return command


def _cylinder_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, CylinderIR):
        raise TypeError(
            "SolidCraft cylinder lowering requires PlacementIR(CylinderIR)"
        )

    _require_positive(primitive.height, "cylinder height")
    _require_positive(primitive.diameter, "cylinder diameter")
    selector = _DirectionSelector(node.anchor)
    base = _cylinder_base_from_anchor(
        primitive.height,
        primitive.diameter,
        primitive.axis,
        node.point,
        selector,
    )
    params = {
        "height": command_value(primitive.height),
        "diameter": command_value(primitive.diameter),
        "base": [command_value(value) for value in base],
        "axis": primitive.axis,
        "operation": operation,
    }
    if operation == "new":
        params["body_name"] = name
    else:
        params["targets"] = [name]
    return _command("solid.cylinder", **params)


def _extrude_commands(node: ExtrudeIR, name: str) -> list[dict]:
    """Lower the qualified Sketch/Profile + Extrude IR slice."""
    sketch = node.sketch
    if sketch.plane not in ("XY", "XZ", "YZ"):
        raise ModelError("portable SolidCraft Sketch IR requires XY, XZ or YZ")
    if len(node.regions) != 1:
        raise ModelError("portable SolidCraft Extrude IR requires one region")

    region = node.regions[0]
    if not isinstance(region, RegionIR):
        raise ModelError("portable SolidCraft Extrude IR requires RegionIR")
    if node.direction not in ("positive", "negative"):
        raise ModelError(
            "portable SolidCraft Extrude IR requires positive or negative direction"
        )

    try:
        pick = _circle_region_interior_point(sketch, region)
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    commands = [
        _command(
            "sketch.create",
            name=sketch.name,
            plane=sketch.plane,
        )
    ]
    for profile in sketch.profiles:
        if not isinstance(profile, CircleProfileIR):
            raise ModelError(
                "portable SolidCraft Extrude IR currently requires CircleProfileIR"
            )
        if tuple(profile.center) != (0, 0):
            raise ModelError(
                "portable SolidCraft CircleProfileIR currently requires origin center"
            )
        _require_positive(profile.diameter, "circle diameter")
        commands.append(
            _command(
                "sketch.circle.center",
                center=[command_value(value) for value in profile.center],
                diameter=command_value(profile.diameter),
            )
        )

    _require_positive(node.distance, "sketch extrusion distance")
    commands.append(_command("sketch.finish"))

    extrude = {
        "body_name": name,
        "direction": node.direction,
        "distance": command_value(node.distance),
    }
    if region.holes:
        extrude["profiles"] = [{"point": [pick[0], pick[1]]}]
        extrude["exact_regions"] = True
    commands.append(_command("solid.extrude", **extrude))
    return commands

def _face_boundary_commands(
    selection: FaceBoundaryIR,
    name: str,
) -> tuple[list[dict], str]:
    if len(selection.faces) != 1:
        raise ModelError(
            "portable SolidCraft face-boundary IR currently requires one face"
        )
    face = selection.faces[0]
    try:
        normal = _FACE_NORMALS[face]
    except KeyError as exc:
        raise ModelError(f"unsupported Forge face in IR: {face!r}") from exc

    face_variable = "$topology_face_1"
    edge_variable = "$topology_edges_1"
    return [
        {
            "command": "model.faces",
            "params": {"body": name},
            "bind": {
                face_variable: {
                    "field": "faces",
                    "where": {"plane_normal": normal},
                    "max": "area",
                }
            },
        },
        {
            "command": "model.edges",
            "params": {"body": name},
            "bind": {
                edge_variable: {
                    "field": "edges",
                    "body": name,
                    "boundary_of": face_variable,
                }
            },
        },
    ], edge_variable


def _portable_commands(model: ModelIR, name: str) -> list[dict]:
    node = model.root
    parameters = _parameter_commands(model)

    if isinstance(node, PlacementIR):
        if isinstance(node.primitive, BoxIR):
            return [*parameters, _box_command(node, name)]
        if isinstance(node.primitive, CylinderIR):
            return [*parameters, _cylinder_command(node, name)]
        raise TypeError(
            f"unsupported SolidCraft placed primitive "
            f"{type(node.primitive).__name__}"
        )

    if isinstance(node, ExtrudeIR):
        return [
            *parameters,
            *_extrude_commands(node, name),
        ]

    if isinstance(node, BooleanSubtractIR):
        return [
            *parameters,
            _csg_box_command(node.target, name),
            _cylinder_command(node.tool, name, operation="cut"),
        ]

    if isinstance(node, ChamferIR):
        _require_positive(node.distance, "chamfer distance")
        topology, edges = _face_boundary_commands(node.edges, name)
        return [
            *parameters,
            _box_command(node.base, name),
            *topology,
            _command(
                "solid.chamfer",
                body=name,
                distance=command_value(node.distance),
                edges=edges,
            ),
        ]

    raise TypeError(f"not a portable Forge IR node: {type(node).__name__}")


def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Lower one normalized Forge model to SolidCraft native intent."""
    if not isinstance(model, ModelIR):
        raise TypeError("SolidCraft backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if isinstance(model.root, LegacyShapeIR):
        return _compile_shape_legacy_with_dependencies(
            model.root.shape,
            name,
        )

    commands = _portable_commands(model, name)
    plain = _plain_command_value(commands)
    document = (
        replay_document(plain)
        if any("bind" in command for command in plain)
        else {"commands": plain}
    )
    return document, _native_dependencies(commands)


def compile_ir(model: ModelIR, name: str) -> dict:
    return compile_ir_with_dependencies(model, name)[0]


__all__ = ["compile_ir", "compile_ir_with_dependencies"]
