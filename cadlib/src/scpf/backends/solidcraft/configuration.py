"""SolidCraft lowering for feature identity and configurations."""
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


from .common import _command


def _body_commands(*args, **kwargs):
    from .dispatch import body_commands
    return body_commands(*args, **kwargs)


def _boolean_command_count(node) -> int:
    """Return SolidCraft geometry command count for one typed Boolean subtree."""
    if isinstance(node, PlacementIR):
        return 1
    if isinstance(node, FilletIR):
        return 2
    if isinstance(node, BooleanIR):
        return _boolean_command_count(node.target) + 1
    raise ModelError(
        "portable SolidCraft Boolean feature references require typed CSG nodes"
    )


def _boolean_feature_command_index(
    root: BooleanIR,
    reference: FeatureRefIR,
) -> int:
    """Map semantic target/tool history roles to backend-local command order."""
    resolve_feature_ref(root, reference)
    segments = reference.path[1:]
    node = root
    offset = 0

    if not segments:
        # A BooleanIR feature is represented natively by the command applying
        # its tool to its target.
        return _boolean_command_count(node.target)

    for position, segment in enumerate(segments):
        last = position == len(segments) - 1
        if not isinstance(node, BooleanIR):
            raise ModelError(
                "SolidCraft feature reference descends beyond Boolean history"
            )
        if segment == "tool":
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a CSG tool"
                )
            return offset + _boolean_command_count(node.target)
        if segment != "target":
            raise ModelError(
                f"unsupported SolidCraft semantic feature role {segment!r}"
            )

        target = node.target
        if isinstance(target, PlacementIR):
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a primitive target"
                )
            return offset
        if isinstance(target, FilletIR):
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a Fillet target"
                )
            return offset + 1
        if not isinstance(target, BooleanIR):
            raise ModelError(
                "SolidCraft feature reference target is not typed Boolean history"
            )
        if last:
            return offset + _boolean_command_count(target.target)
        node = target

    raise ModelError("SolidCraft feature reference did not resolve to a command")


def _history_command_indexes(commands: list[dict]) -> list[int]:
    """Return backend-local native history commands, excluding helpers."""
    return [
        index
        for index, command in enumerate(commands)
        if command.get("command", "").startswith(("solid.", "sheet."))
    ]


def _semantic_feature_command_index(
    model: ModelIR,
    reference: FeatureRefIR,
    commands: list[dict],
    name: str,
) -> int:
    """Map one semantic feature reference to the current native command list."""
    if isinstance(model.root, BooleanIR):
        geometry_index = _boolean_feature_command_index(model.root, reference)
        return len(model.parameters) + geometry_index

    resolved = resolve_feature_ref(model.root, reference)
    if not isinstance(resolved, BodyIR):
        raise ModelError("semantic feature reference does not resolve to BodyIR")

    prefix = _body_commands(model, resolved, name)
    prefix_history = _history_command_indexes(prefix)
    full_history = _history_command_indexes(commands)
    if not prefix_history or len(prefix_history) > len(full_history):
        raise ModelError(
            "semantic feature reference has no matching SolidCraft history command"
        )
    return full_history[len(prefix_history) - 1]


def _configured_feature_command_index(
    model: ModelIR,
    configuration: ConfigurationIR,
    commands: list[dict],
    name: str,
) -> int:
    """Resolve one qualified configuration feature through semantic identity."""
    if (
        len(configuration.columns) != 1
        or not isinstance(configuration.columns[0], SuppressionColumnIR)
    ):
        raise ModelError(
            "portable SolidCraft configuration requires one suppression feature"
        )
    return _semantic_feature_command_index(
        model,
        configuration.columns[0].feature,
        commands,
        name,
    )


def _portable_named_feature_commands(
    model: ModelIR,
    commands: list[dict],
    name: str,
) -> list[dict]:
    """Apply public feature() initial suppression through semantic identity."""
    commands = [dict(command) for command in commands]
    for feature in model.named_features:
        if not isinstance(feature, NamedFeatureIR):
            raise ModelError("invalid semantic named feature")
        if not feature.suppressed:
            continue
        index = _semantic_feature_command_index(
            model,
            feature.feature,
            commands,
            name,
        )
        variable = f"$feature_{feature.name}_name"
        target = dict(commands[index])
        bindings = dict(target.get("bind", {}))
        if variable in bindings:
            raise ModelError(f"duplicate named feature {feature.name!r}")
        bindings[variable] = "name"
        target["bind"] = bindings
        commands[index] = target
        commands.append(
            _command(
                "timeline.suppress",
                features=[variable],
                suppressed=True,
            )
        )
    return commands


def _portable_configuration_commands(
    model: ModelIR,
    configuration: ConfigurationIR,
    commands: list[dict],
    name: str,
) -> list[dict]:
    """Lower semantic suppression rows without source-object/native-id lookup."""
    from ..configurations import _row_variable

    commands = [dict(command) for command in commands]
    index = _configured_feature_command_index(
        model, configuration, commands, name
    )

    feature_name = "$config_name_1"
    target = dict(commands[index])
    bindings = dict(target.get("bind", {}))
    bindings[feature_name] = "name"
    target["bind"] = bindings
    commands[index] = target

    commands.append(
        _command(
            "config.configure",
            features=[feature_name],
        )
    )

    def row_binding(variable, row_name):
        return {
            variable: {
                "field": "rows",
                "where": {"name": row_name},
                "select": "id",
            }
        }

    row_refs = {}
    first = configuration.rows[0].name
    if first != "Default":
        rename = _command(
            "config.row",
            name="Default",
            rename=first,
        )
        variable = _row_variable(first)
        rename["bind"] = row_binding(variable, first)
        row_refs[first] = variable
        commands.append(rename)

    for row in configuration.rows:
        update = _command(
            "config.row",
            name=row.name,
            values={
                f"suppress:{feature_name}": (
                    "true" if row.cells[0] else "false"
                ),
            },
        )
        if row.name not in row_refs:
            variable = _row_variable(row.name)
            update["bind"] = row_binding(variable, row.name)
            row_refs[row.name] = variable
        commands.append(update)

    commands.append(
        _command(
            "config.activate",
            row=row_refs[configuration.active],
        )
    )
    commands.append(_command("config.table"))
    return commands
