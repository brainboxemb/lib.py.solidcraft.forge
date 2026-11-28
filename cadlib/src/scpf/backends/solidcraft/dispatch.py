"""Small SolidCraft backend dispatcher over semantic IR domains."""
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


from .common import _parameter_commands
from .primitives import (
    _box_command, _cylinder_command, _cone_command, _sphere_command,
    _csg_primitive_command,
)
from .features import (
    _hole_commands, _plastic_feature_commands,
    _rectangular_pattern_commands, _circular_pattern_commands,
)
from .operations import (
    _fillet_commands, _translated_body_ir, _boolean_commands,
    _extrude_commands, _revolve_commands, _chamfer_commands, _shell_commands,
)
from .sheet_metal import (
    _sheet_base_commands, _sheet_contour_commands, _sheet_fold_commands,
    _sheet_edge_flange_commands, _sheet_hem_commands,
    _sheet_path_flange_commands, _sheet_perforate_commands,
)
from .configuration import (
    _portable_named_feature_commands, _portable_configuration_commands,
)


def body_commands(model: ModelIR, node: BodyIR, name: str) -> list[dict]:
    """Lower one typed semantic body history without re-reading Shape.data."""
    if isinstance(node, SheetBaseIR):
        return _sheet_base_commands(model, node, name)

    if isinstance(node, SheetContourFlangeIR):
        return _sheet_contour_commands(model, node, name)

    if isinstance(node, SheetFoldIR):
        return _sheet_fold_commands(model, node, name)

    if isinstance(node, SheetEdgeFlangeIR):
        return _sheet_edge_flange_commands(model, node, name)

    if isinstance(node, SheetHemIR):
        return _sheet_hem_commands(model, node, name)

    if isinstance(node, SheetPathFlangeIR):
        return _sheet_path_flange_commands(model, node, name)

    if isinstance(node, SheetPerforateIR):
        return _sheet_perforate_commands(model, node, name)

    if isinstance(node, TranslationIR):
        return _body_commands(
            model,
            _translated_body_ir(node.body, node.offset),
            name,
        )

    if isinstance(node, PlacementIR):
        if node.source_kind == "translated":
            return [_csg_primitive_command(node, name, "new")]
        if isinstance(node.primitive, BoxIR):
            return [_box_command(node, name)]
        if isinstance(node.primitive, CylinderIR):
            return [_cylinder_command(node, name)]
        if isinstance(node.primitive, ConeIR):
            return [_cone_command(node, name)]
        if isinstance(node.primitive, SphereIR):
            return [_sphere_command(node, name)]
        raise TypeError(
            f"unsupported SolidCraft placed primitive "
            f"{type(node.primitive).__name__}"
        )

    if isinstance(node, ExtrudeIR):
        return _extrude_commands(model, node, name)

    if isinstance(node, BooleanIR):
        return _boolean_commands(model, node, name)

    if isinstance(node, HoleIR):
        return _hole_commands(model, node, name)

    if isinstance(node, PlasticFeatureIR):
        return _plastic_feature_commands(model, node, name)

    if isinstance(node, FilletIR):
        return _fillet_commands(model, node, name)

    if isinstance(node, RevolveIR):
        return _revolve_commands(model, node, name)

    if isinstance(node, ChamferIR):
        return _chamfer_commands(model, node, name)

    if isinstance(node, ShellIR):
        return _shell_commands(model, node, name)

    if isinstance(node, RectangularPatternIR):
        return _rectangular_pattern_commands(model, node, name)

    if isinstance(node, CircularPatternIR):
        return _circular_pattern_commands(model, node, name)

    raise TypeError(f"not a portable Forge BodyIR node: {type(node).__name__}")


def _portable_commands(model: ModelIR, name: str) -> list[dict]:
    node = model.root
    if not isinstance(node, BodyIR):
        raise TypeError(f"not a portable Forge IR node: {type(node).__name__}")
    return [
        *_parameter_commands(model),
        *_body_commands(model, node, name),
    ]


def compile_ir_commands_with_dependencies(model: ModelIR, name: str):
    """Lower one ModelIR to a flat native command sequence.

    This is the shared SolidCraft boundary used both for a standalone design
    and for one reusable component definition inside AssemblyIR. Replay
    wrapping belongs to the enclosing design, so native occurrence/component
    transport never needs to enter semantic ModelIR.
    """
    if not isinstance(model, ModelIR):
        raise TypeError("SolidCraft backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if isinstance(model.root, LegacyShapeIR):
        from ...compiler import _compile_model_commands
        commands = _compile_model_commands(model.root.shape, name)
        return commands, _native_dependencies(commands)

    commands = _portable_commands(model, name)
    if model.named_features:
        commands = _portable_named_feature_commands(
            model,
            commands,
            name,
        )
    if model.configuration is not None:
        commands = _portable_configuration_commands(
            model,
            model.configuration,
            commands,
            name,
        )
    return commands, _native_dependencies(commands)


def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Lower one normalized Forge model to SolidCraft native intent."""
    commands, dependencies = compile_ir_commands_with_dependencies(
        model,
        name,
    )
    plain = _plain_command_value(commands)
    document = (
        replay_document(plain)
        if any("bind" in command for command in plain)
        else {"commands": plain}
    )
    return document, dependencies


def compile_ir(model: ModelIR, name: str) -> dict:
    return compile_ir_with_dependencies(model, name)[0]


__all__ = [
    "compile_ir",
    "compile_ir_with_dependencies",
    "compile_ir_commands_with_dependencies",
]


_body_commands = body_commands
