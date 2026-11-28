"""SolidCraft lowering for sheet-metal semantic IR."""
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


from .common import _require_positive, _command, _role_command_value
from .sketch import (
    _solidcraft_sketch_create,
    _solidcraft_profile_commands,
    _solidcraft_dimension_sum,
    _sketch_chain_geometry_commands,
)


def _body_commands(*args, **kwargs):
    from .dispatch import body_commands
    return body_commands(*args, **kwargs)


def _sheet_rule_command(model: ModelIR, rule: SheetRuleIR) -> dict:
    if not isinstance(rule, SheetRuleIR):
        raise ModelError("typed sheet body requires SheetRuleIR")
    _require_positive(rule.thickness, "sheet metal thickness")
    _require_positive(rule.bend_radius, "sheet metal bend radius")
    k = pv(rule.k_factor)
    if not isfinite(k) or not 0 < k < 1:
        raise ModelError("sheet metal k_factor must be between 0 and 1")
    return _command(
        "sheet.manage_rules",
        name=rule.name,
        thickness=_role_command_value(model, rule.thickness, "length"),
        k_factor=_role_command_value(model, rule.k_factor, "ratio"),
        bend_radius=_role_command_value(model, rule.bend_radius, "length"),
        active=True,
    )


def _sheet_chain_commands(
    model: ModelIR,
    chain: SketchChainIR,
    *,
    bind_curves: bool = False,
) -> tuple[list[dict], str | None]:
    """Lower semantic connected Sketch intent with its standalone support."""
    if not isinstance(chain, SketchChainIR):
        raise ModelError("sheet Sketch path requires SketchChainIR")
    if chain.plane is None:
        raise ModelError("sheet Sketch path requires semantic PlaneIR support")
    geometry, curve_variable = _sketch_chain_geometry_commands(
        chain,
        model=model,
        bind_curves=bind_curves,
    )
    return [
        _solidcraft_sketch_create(chain),
        *geometry,
        _command("sketch.finish"),
    ], curve_variable


def _sheet_base_commands(
    model: ModelIR,
    node: SheetBaseIR,
    name: str,
) -> list[dict]:
    rule = _sheet_rule_command(model, node.rule)
    blank = node.blank
    if isinstance(blank, SketchChainIR):
        if not blank.closed:
            raise ModelError("sheet base chain must be closed")
        sketch, _curves = _sheet_chain_commands(model, blank)
        sketch_name = blank.name
    else:
        if len(blank.profiles) != 1:
            raise ModelError("typed sheet base requires one closed profile")
        sketch = [_solidcraft_sketch_create(blank)]
        sketch.extend(
            _solidcraft_profile_commands(
                blank,
                blank.profiles[0],
                profile_index=1,
            )
        )
        sketch.append(_command("sketch.finish"))
        sketch_name = blank.name
    return [
        rule,
        *sketch,
        _command(
            "sheet.flange",
            type="base",
            sketch=sketch_name,
            rule=node.rule.name,
            body_name=name,
        ),
    ]


def _sheet_contour_commands(
    model: ModelIR,
    node: SheetContourFlangeIR,
    name: str,
) -> list[dict]:
    rule = _sheet_rule_command(model, node.rule)
    sketch, curves = _sheet_chain_commands(
        model,
        node.contour,
        bind_curves=True,
    )
    params = {
        "type": "contour",
        "sketch": node.contour.name,
        "curves": curves,
        "distance": _role_command_value(model, node.distance, "length"),
        "rule": node.rule.name,
        "body_name": name,
    }
    if node.flip:
        params["flip"] = True
    if node.reverse:
        params["reverse"] = True
    return [rule, *sketch, _command("sheet.flange", **params)]


def _sheet_fold_commands(
    model: ModelIR,
    node: SheetFoldIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "angle": _role_command_value(model, node.angle, "angle"),
        "position": node.position,
        "flip": node.flip,
        "body": name,
    }
    if isinstance(node.line, SketchChainIR):
        sketch, _curves = _sheet_chain_commands(model, node.line)
        commands.extend(sketch)
        params["sketch"] = node.line.name
        params["curve"] = "l1"
    else:
        params["points"] = [
            [command_value(value) for value in point]
            for point in node.line
        ]
    if node.fixed is not None:
        params["fixed"] = [command_value(value) for value in node.fixed]
    return [*commands, _command("sheet.fold", **params)]


def _sheet_edge_flange_commands(
    model: ModelIR,
    node: SheetEdgeFlangeIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "type": "edge",
        "edges": [
            [command_value(value) for value in point]
            for point in node.edges
        ],
        "height": _role_command_value(model, node.height, "length"),
        "angle": _role_command_value(model, node.angle, "angle"),
        "body": name,
    }
    if node.height_from is not None:
        params["height_from"] = node.height_from
    if node.position is not None:
        params["position"] = node.position
    if node.flip:
        params["flip"] = True
    return [*commands, _command("sheet.flange", **params)]


def _sheet_hem_commands(
    model: ModelIR,
    node: SheetHemIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "edges": [
            [command_value(value) for value in point]
            for point in node.edges
        ],
        "length": _role_command_value(model, node.length, "length"),
        "body": name,
    }
    if node.gap is not None:
        params["gap"] = _role_command_value(model, node.gap, "length")
    if node.flip:
        params["flip"] = True
    return [*commands, _command("sheet.hem", **params)]


def _sheet_path_flange_commands(
    model: ModelIR,
    node: SheetPathFlangeIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    sketch, curves = _sheet_chain_commands(
        model,
        node.path,
        bind_curves=True,
    )
    params = {
        "edge": [command_value(value) for value in node.edge],
        "sketch": node.path.name,
        "curves": curves,
        "body": name,
    }
    if node.radius is not None:
        params["radius"] = _role_command_value(
            model,
            node.radius,
            "length",
        )
    return [
        *commands,
        *sketch,
        _command("sheet.path_flange", **params),
    ]


def _sheet_perforate_commands(
    model: ModelIR,
    node: SheetPerforateIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "diameter": _role_command_value(model, node.diameter, "length"),
        "pitch": _role_command_value(model, node.pitch, "length"),
        "body": name,
    }
    if node.margin is not None:
        params["margin"] = _role_command_value(model, node.margin, "length")
    if node.pattern != "staggered":
        params["pattern"] = node.pattern
    return [*commands, _command("sheet.perforate", **params)]
