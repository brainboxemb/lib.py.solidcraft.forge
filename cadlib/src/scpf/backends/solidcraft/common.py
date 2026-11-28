"""Shared SolidCraft lowering helpers."""
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


def _role_scalar_expression_text(
    model: ModelIR,
    node,
    role: str,
    *,
    scalar_literal: bool = False,
) -> str:
    """Render bounded semantic scalar IR for one typed SolidCraft use site."""
    unit = {
        "length": "mm",
        "angle": "deg",
        "count": "",
        "ratio": "",
    }.get(role)
    if unit is None:
        raise ModelError(f"unsupported Forge parameter role {role!r}")
    parameters = {parameter.name: parameter for parameter in model.parameters}

    if isinstance(node, ScalarLiteralIR):
        text = number_text(node.value)
        if scalar_literal or not unit:
            return text
        return f"{text} {unit}"

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
            return (
                f"{node.name} * 1 {unit}"
                if unit
                else f"{node.name} * 1"
            )
        return node.name

    if isinstance(node, ScalarUnaryIR):
        if node.operation != "negate":
            raise ModelError(
                f"unsupported scalar unary operation {node.operation!r}"
            )
        return (
            f"-({_role_scalar_expression_text(model, node.operand, role)})"
        )

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


def _role_command_value(model: ModelIR, value, role: str):
    """Spell one typed use of a mixed-role source parameter or expression."""
    if role not in {"length", "angle", "count", "ratio"}:
        raise ModelError(f"unsupported Forge parameter role {role!r}")

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
