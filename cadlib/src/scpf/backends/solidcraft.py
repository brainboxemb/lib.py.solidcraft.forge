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
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    command_value,
    number_text,
)
from ..ir import (
    BoxIR,
    ChamferIR,
    CircleExtrudeIR,
    FaceBoundaryIR,
    LegacyShapeIR,
    ModelIR,
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
    """Match the stable SolidCraft symbolic half-expression spelling."""
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


def _box_corner(node: BoxIR):
    dimensions = (node.length, node.width, node.height)
    corner = []
    for dimension, side in zip(dimensions, node.anchor):
        if side < 0:
            corner.append(0)
        elif side > 0:
            corner.append(_negative_value(dimension))
        else:
            corner.append(_negative_half(dimension))
    return corner


def _box_command(node: BoxIR, name: str) -> dict:
    _require_positive(node.length, "box length")
    _require_positive(node.width, "box width")
    _require_positive(node.height, "box height")

    params = {
        "length": command_value(node.length),
        "width": command_value(node.width),
        "height": command_value(node.height),
    }
    _DirectionSelector(node.anchor)
    if node.anchor == (0, 0, 0):
        params["center"] = [0, 0, 0]
    else:
        params["corner"] = [
            command_value(value)
            for value in _box_corner(node)
        ]
    params["body_name"] = name
    return _command("solid.box", **params)


def _circle_extrude_commands(node: CircleExtrudeIR, name: str) -> list[dict]:
    _require_positive(node.diameter, "circle diameter")
    _require_positive(node.distance, "sketch extrusion distance")
    return [
        _command(
            "sketch.create",
            name=node.sketch_name,
            plane=node.plane,
        ),
        _command(
            "sketch.circle.center",
            center=[0, 0],
            diameter=command_value(node.diameter),
        ),
        _command("sketch.finish"),
        _command(
            "solid.extrude",
            body_name=name,
            direction=node.direction,
            distance=command_value(node.distance),
        ),
    ]


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

    if isinstance(node, BoxIR):
        return [*parameters, _box_command(node, name)]

    if isinstance(node, CircleExtrudeIR):
        return [
            *parameters,
            *_circle_extrude_commands(node, name),
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
