"""Shared Mitcad lowering helpers."""
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
