"""Feature-reference, configuration and configured-design normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from ...core import Shape
from ..base import BodyIR
from ..body import BooleanIR, IRNode, LegacyShapeIR, ShellIR, TranslationIR
from ..configuration import (
    ConfiguredDesignIR,
    ConfigurationIR,
    ConfigurationRowIR,
    FeatureRefIR,
    ModelIR,
    NamedFeatureIR,
    ParameterCellIR,
    ParameterColumnIR,
    SuppressionColumnIR,
)
from ..features import CircularPatternIR, HoleIR, PlasticFeatureIR, RectangularPatternIR
from ..operations import ChamferIR, FilletIR, RevolveIR
from .body import _normalize_node
from .values import _parameter_ir

def resolve_feature_ref(root: IRNode, reference: FeatureRefIR) -> IRNode:
    """Resolve one semantic feature path without backend/native identity."""
    if not isinstance(reference, FeatureRefIR):
        raise TypeError("feature reference resolution requires FeatureRefIR")
    if reference.path[0] != "root":
        raise ValueError("FeatureRefIR path must begin at root")

    node = root
    for segment in reference.path[1:]:
        if isinstance(node, TranslationIR) and segment == "body":
            node = node.body
            continue
        if isinstance(node, BooleanIR) and segment in {"target", "tool"}:
            node = getattr(node, segment)
            continue
        if isinstance(node, (HoleIR, PlasticFeatureIR)) and segment == "target":
            node = node.target
            continue
        if isinstance(node, (ChamferIR, FilletIR, ShellIR)) and segment == "base":
            node = node.base
            continue
        if (
            isinstance(node, RevolveIR)
            and segment == "target"
            and node.target is not None
        ):
            node = node.target
            continue
        if isinstance(
            node,
            (RectangularPatternIR, CircularPatternIR),
        ) and segment == "base":
            node = node.base
            continue
        raise ValueError(
            f"FeatureRefIR path segment {segment!r} is not valid for "
            f"{type(node).__name__}"
        )
    return node


def _pattern_authored_feature_ref(
    design: Shape,
    root: BodyIR,
    feature: Shape,
    *,
    path: tuple[str, ...] = ("root",),
) -> FeatureRefIR | None:
    """Map exact authored source identity to semantic body-history roles."""
    if design is feature:
        return FeatureRefIR(path=path)

    if design.kind in {"exported_feature", "named_feature"}:
        source = design.data[0]
        return _pattern_authored_feature_ref(
            source,
            root,
            feature,
            path=path,
        )

    if (
        isinstance(root, (HoleIR, PlasticFeatureIR, BooleanIR))
        and design.kind in {"union", "difference", "intersection"}
    ):
        target_shape, tool_shape = design.data
        while tool_shape.kind == "exported_feature":
            tool_shape, _name = tool_shape.data
        if feature is tool_shape:
            return FeatureRefIR(path=path)
        target = root.target
        if isinstance(target, BodyIR):
            return _pattern_authored_feature_ref(
                target_shape,
                target,
                feature,
                path=(*path, "target"),
            )
        return None

    if (
        isinstance(root, (ChamferIR, FilletIR, ShellIR))
        and design.kind in {"chamfer", "fillet", "shell"}
    ):
        base_shape = design.data[0]
        return _pattern_authored_feature_ref(
            base_shape,
            root.base,
            feature,
            path=(*path, "base"),
        )

    if (
        isinstance(root, RevolveIR)
        and root.operation == "cut"
        and design.kind == "difference"
    ):
        target_shape, tool_shape = design.data
        if feature is tool_shape:
            return FeatureRefIR(path=path)
        if isinstance(root.target, BodyIR):
            return _pattern_authored_feature_ref(
                target_shape,
                root.target,
                feature,
                path=(*path, "target"),
            )
        return None

    if (
        isinstance(root, (RectangularPatternIR, CircularPatternIR))
        and design.kind in {"rectangular_pattern", "circular_pattern"}
    ):
        original = design.data[0]
        return _pattern_authored_feature_ref(
            original,
            root.base,
            feature,
            path=(*path, "base"),
        )

    return None


def _boolean_authored_feature_ref(
    design: Shape,
    root: BooleanIR,
    feature: Shape,
    *,
    path: tuple[str, ...] = ("root",),
) -> FeatureRefIR | None:
    """Map authored CSG object identity to typed semantic history roles."""
    if design is feature:
        return FeatureRefIR(path=path)
    if design.kind in {"exported_feature", "named_feature"}:
        return _boolean_authored_feature_ref(
            design.data[0],
            root,
            feature,
            path=path,
        )
    if design.kind not in {"union", "difference", "intersection"}:
        return None

    target_shape, tool_shape = design.data
    if feature is tool_shape:
        return FeatureRefIR(path=(*path, "tool"))

    if feature is target_shape and isinstance(root.target, BodyIR):
        return FeatureRefIR(path=(*path, "target"))

    if isinstance(root.target, BooleanIR):
        nested = _boolean_authored_feature_ref(
            target_shape,
            root.target,
            feature,
            path=(*path, "target"),
        )
        if nested is not None:
            return nested

    if isinstance(root.tool, BooleanIR):
        nested = _boolean_authored_feature_ref(
            tool_shape,
            root.tool,
            feature,
            path=(*path, "tool"),
        )
        if nested is not None:
            return nested
    return None


def _configuration_feature_ref(
    design: Shape,
    feature: Shape,
    root: IRNode,
) -> FeatureRefIR:
    """Resolve authored identity to semantic IR before native ids exist."""
    if feature is design and isinstance(root, BodyIR):
        return FeatureRefIR(path=("root",))

    if isinstance(root, TranslationIR) and design.kind == "translated":
        child, _offset = design.data
        reference = _configuration_feature_ref(
            child,
            feature,
            root.body,
        )
        translated = FeatureRefIR(
            path=("root", "body", *reference.path[1:]),
        )
        resolve_feature_ref(root, translated)
        return translated

    # Keep the already-qualified #424 authored Revolve-cut identity stable: the
    # source tool becomes the semantic root feature rather than a Boolean tool.
    if (
        isinstance(root, RevolveIR)
        and root.operation == "cut"
        and design.kind == "difference"
    ):
        _target, authored_tool = design.data
        if feature is not authored_tool:
            raise ValueError(
                "suppression feature is not the authored root Revolve feature"
            )
        return FeatureRefIR(path=("root",))

    if isinstance(root, BooleanIR):
        reference = _boolean_authored_feature_ref(design, root, feature)
        if reference is not None:
            # Resolve immediately so malformed semantic paths fail during
            # frontend normalization rather than in a backend.
            resolve_feature_ref(root, reference)
            return reference
        raise ValueError(
            "suppression feature is not a member of the typed Boolean history"
        )

    if isinstance(root, BodyIR):
        reference = _pattern_authored_feature_ref(
            design,
            root,
            feature,
        )
        if reference is not None:
            resolve_feature_ref(root, reference)
            return reference

    raise ValueError(
        "portable suppression requires a qualified semantic feature history"
    )


def _normalize_configuration(configured, feature_resolver) -> ConfigurationIR:
    """Normalize the v0.26 final-model configuration table semantics."""
    from ...configurations import (
        _Configuration,
        _ParameterColumn,
        _SuppressionColumn,
    )

    if not isinstance(configured, _Configuration):
        raise TypeError("configuration normalization requires _Configuration")

    columns = []
    for column in configured.columns:
        if isinstance(column, _ParameterColumn):
            columns.append(ParameterColumnIR(column.name))
        elif isinstance(column, _SuppressionColumn):
            columns.append(
                SuppressionColumnIR(
                    feature=feature_resolver(column.feature)
                )
            )
        else:
            raise ValueError(
                "configuration column is outside current public semantics"
            )

    rows = []
    for name, cells in configured.rows:
        converted = []
        for column, cell in zip(columns, cells):
            if isinstance(column, SuppressionColumnIR):
                if cell == "true":
                    converted.append(True)
                elif cell == "false":
                    converted.append(False)
                else:
                    raise ValueError(
                        "suppression configuration cell must be bool"
                    )
            else:
                converted.append(ParameterCellIR(cell))
        rows.append(
            ConfigurationRowIR(
                name=name,
                cells=tuple(converted),
            )
        )

    return ConfigurationIR(
        active=configured.active,
        columns=tuple(columns),
        rows=tuple(rows),
    )


def _authored_assembly(value):
    """Return one authored Assembly without importing backend assembly lowering."""
    from ...model_objects import Assembly, ModelInstance

    if isinstance(value, ModelInstance):
        return Assembly((value,))
    if isinstance(value, Assembly):
        return value
    raise TypeError(
        "configured assembly target must be ModelInstance or Assembly"
    )


def _assembly_configuration_feature_ref(
    authored_design,
    assembly_ir,
    feature,
):
    """Resolve assembly suppression identity to semantic definition identity."""
    from ...assembly_ir import ComponentFeatureRefIR
    from ...model_objects import _ComponentFeatureReference

    assembly = _authored_assembly(authored_design)
    definition_ids = {}
    definition_instances = {}
    for instance in assembly.instances:
        key = instance.definition.key
        if key in definition_ids:
            continue
        definition_ids[key] = f"definition_{len(definition_ids) + 1}"
        definition_instances[key] = instance

    if isinstance(feature, _ComponentFeatureReference):
        try:
            definition_id = definition_ids[feature.definition_key]
        except KeyError as exc:
            raise ValueError(
                "component feature reference is not part of configured design"
            ) from exc
        definition = next(
            item
            for item in assembly_ir.definitions
            if item.id == definition_id
        )
        if feature.name not in definition.exported_features:
            raise ValueError(
                f"component definition has no exported feature {feature.name!r}"
            )
        return ComponentFeatureRefIR(
            definition=definition_id,
            name=feature.name,
        )

    if not isinstance(feature, Shape):
        raise ValueError(
            "assembly suppression requires Shape or exported component feature"
        )

    exported_matches = []
    for key, instance in definition_instances.items():
        for name, exported in instance.definition.features:
            if feature is exported:
                exported_matches.append(
                    ComponentFeatureRefIR(
                        definition=definition_ids[key],
                        name=name,
                    )
                )
    if len(exported_matches) == 1:
        return exported_matches[0]
    if len(exported_matches) > 1:
        raise ValueError(
            "exported suppression Shape is ambiguous across component definitions"
        )

    raise ValueError(
        "Assembly suppression Shape must be an explicitly exported component feature"
    )


def _named_feature_ir(design: Shape, root: IRNode) -> tuple[NamedFeatureIR, ...]:
    """Collect public feature() identity/state without backend-native names."""
    found = []

    def visit(value):
        if isinstance(value, Shape):
            if value.kind == "named_feature":
                _source, name, suppressed = value.data
                reference = _configuration_feature_ref(
                    design,
                    value,
                    root,
                )
                found.append(
                    NamedFeatureIR(
                        name=name,
                        feature=reference,
                        suppressed=suppressed,
                    )
                )
                visit(value.data[0])
                return
            visit(value.data)
            return
        if isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    visit(design)
    return tuple(found)


def normalize_configured_design(
    design,
) -> ModelIR | ConfiguredDesignIR:
    """Normalize v0.26 final-model configuration over Shape or Assembly."""
    from ...configurations import _Configuration
    from ...model_objects import Assembly, ModelInstance

    configured = getattr(design, "_configuration", None)
    if not isinstance(configured, _Configuration):
        raise TypeError(
            "configured Forge IR normalization requires final-model configuration"
        )

    if isinstance(design, Shape):
        root = _normalize_node(design)
        if isinstance(root, LegacyShapeIR):
            raise ValueError(
                "configured design is outside the qualified portable IR slice"
            )
        configuration = _normalize_configuration(
            configured,
            lambda feature: _configuration_feature_ref(
                design,
                feature,
                root,
            ),
        )
        return ModelIR(
            root=root,
            parameters=_parameter_ir(design),
            configuration=configuration,
            named_features=_named_feature_ir(design, root),
        )

    if isinstance(design, (ModelInstance, Assembly)):
        from ...assembly_ir import normalize_assembly

        assembly_ir = normalize_assembly(design)
        configuration = _normalize_configuration(
            configured,
            lambda feature: _assembly_configuration_feature_ref(
                design,
                assembly_ir,
                feature,
            ),
        )
        return ConfiguredDesignIR(
            design=assembly_ir,
            configuration=configuration,
        )

    raise TypeError(
        "configured design target is outside current public semantics"
    )
