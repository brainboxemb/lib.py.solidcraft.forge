"""Small Mitcad backend dispatcher over semantic IR domains."""
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


from .common import _parameter_commands
from .primitives import (
    _box_command, _cylinder_command, _cone_commands, _sphere_commands,
)
from .operations import (
    _boolean_command_plan, _extrude_commands, _revolve_commands,
    _revolve_cut_document, _fillet_document, _chamfer_document,
    _materialize_translations, _contains_translation,
)
from .configuration import _mitcad_configuration_commands, _qualified_configuration_slice

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


def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Compile the qualified Forge semantic IR subset to Mitcad intent."""
    if not isinstance(model, ModelIR):
        raise TypeError("Mitcad backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    node = model.root
    if any(feature.suppressed for feature in model.named_features):
        raise ModelError(
            "Mitcad backend does not support initially suppressed named features"
        )
    if (
        model.configuration is not None
        and not _qualified_configuration_slice(model.configuration)
    ):
        raise ModelError(
            "Mitcad backend does not support Forge configurations outside "
            "the qualified single-suppression slice"
        )
    if isinstance(node, LegacyShapeIR):
        raise ModelError(
            "Mitcad backend does not yet support Forge shape kind "
            f"{node.source_kind!r}; no qualified semantic IR lowering exists"
        )

    if model.configuration is not None and _contains_translation(node):
        raise ModelError(
            "Mitcad configured TranslationIR feature identity is not qualified yet"
        )
    node = _materialize_translations(node)

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
