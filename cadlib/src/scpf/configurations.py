"""Document-level native SolidCraft configuration-table intent and lowering."""

from dataclasses import dataclass
import hashlib
from math import isfinite

from .core import Expression, Parameter, Shape, command_value, number_text, parameters_in


@dataclass(frozen=True)
class _ParameterColumn:
    name: str


@dataclass(frozen=True)
class _SuppressionColumn:
    feature: object


@dataclass(frozen=True)
class _AlwaysCondition:
    pass


@dataclass(frozen=True)
class _DriveParameterEffect:
    parameter: _ParameterColumn
    expression: object


@dataclass(frozen=True)
class _ConfigurationRule:
    id: str
    name: str
    enabled: bool
    condition: object
    effect: object


@dataclass(frozen=True)
class _ConfiguredDesign:
    design: object
    active: str
    columns: tuple
    rows: tuple
    rules: tuple = ()


def Param(name):
    """Select an existing native model parameter as a configuration column."""
    if isinstance(name, Parameter):
        name = name.name
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError("Param requires a native parameter name")
    return _ParameterColumn(name)


def Suppress(feature):
    """Select one exact Forge-authored feature as a suppression column."""
    from .model_objects import _ComponentFeatureReference
    if not isinstance(feature, (Shape, _ComponentFeatureReference)):
        raise TypeError(
            "Suppress requires an authored feature Shape or component feature reference"
        )
    return _SuppressionColumn(feature)


def Always():
    """Match every configuration activation for one native configuration rule."""
    return _AlwaysCondition()


def _configuration_expression(value):
    """Normalize one native configuration parameter expression."""
    if isinstance(value, (Parameter, Expression)):
        return str(command_value(value))
    if isinstance(value, str) and value.strip():
        return value
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    ):
        return number_text(value)
    raise TypeError(
        "configuration parameter expressions require a finite number, "
        "non-empty expression string, Parameter or Expression"
    )


def DriveParameter(parameter, expression):
    """Drive one configured parameter while a configuration rule matches."""
    if not isinstance(parameter, _ParameterColumn):
        parameter = Param(parameter)
    _configuration_expression(expression)
    return _DriveParameterEffect(parameter, expression)


def ConfigRule(rule_id, name, *, enabled=True, condition, effect):
    """Author one typed native SolidCraft Configuration Rule.

    The initial public rule slice supports Always() plus DriveParameter(...).
    Rule enablement is the native independent checkbox state; it is not a
    boolean model parameter and does not create another configuration row axis.
    """
    if (
        not isinstance(rule_id, str)
        or not rule_id.strip()
        or rule_id != rule_id.strip()
        or len(rule_id) > 64
    ):
        raise ValueError("configuration rule id must be 1..64 non-space characters")
    if (
        not isinstance(name, str)
        or not name.strip()
        or name != name.strip()
        or len(name) > 128
    ):
        raise ValueError("configuration rule name must be 1..128 non-space characters")
    if not isinstance(enabled, bool):
        raise TypeError("configuration rule enabled must be bool")
    if not isinstance(condition, _AlwaysCondition):
        raise TypeError("configuration rule condition must use Always()")
    if not isinstance(effect, _DriveParameterEffect):
        raise TypeError("configuration rule effect must use DriveParameter()")
    return _ConfigurationRule(rule_id, name, enabled, condition, effect)


def Configure(design, *, active, columns, rows, rules=()):
    """Return one final design with an editable native configuration table.

    Each row contains one parameter expression or suppression boolean per
    column, in column order. The active name must be one of the declared rows.

    Optional ConfigRule entries remain orthogonal to the row axis. A native
    enabled rule may drive a configured parameter after row activation; turning
    that rule off restores the row's stored expression.
    """
    from .model_objects import Assembly, ModelInstance
    if not isinstance(design, (Shape, ModelInstance, Assembly)):
        raise TypeError(
            "Configure requires a final Shape, component occurrence or Assembly"
        )
    columns = tuple(columns)
    if not columns or not all(isinstance(c, (_ParameterColumn, _SuppressionColumn))
                              for c in columns):
        raise TypeError("Configure columns must contain Param or Suppress")
    keys = [("param", c.name) if isinstance(c, _ParameterColumn)
            else ("feature", id(c.feature)) for c in columns]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate configuration column")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("Configure requires an ordered mapping of named rows")
    normalized = []
    for name, cells in rows.items():
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError("configuration row names must be non-empty text")
        cells = tuple(cells)
        if len(cells) != len(columns):
            raise ValueError(f"configuration {name!r} has the wrong cell count")
        converted = []
        for column, cell in zip(columns, cells):
            if isinstance(column, _SuppressionColumn):
                if not isinstance(cell, bool):
                    raise TypeError("suppression cells must be bool")
                converted.append("true" if cell else "false")
            elif isinstance(cell, str) and cell.strip():
                converted.append(cell)
            elif isinstance(cell, (int, float)) and not isinstance(cell, bool) and isfinite(cell):
                converted.append(number_text(cell))
            else:
                raise TypeError("parameter cells require a finite number or expression")
        normalized.append((name, tuple(converted)))
    if active not in rows:
        raise ValueError("active configuration must name a declared row")

    try:
        rules = tuple(rules)
    except TypeError as exc:
        raise TypeError("Configure rules must contain ConfigRule entries") from exc
    if not all(isinstance(rule, _ConfigurationRule) for rule in rules):
        raise TypeError("Configure rules must contain ConfigRule entries")
    if len({rule.id for rule in rules}) != len(rules):
        raise ValueError("duplicate configuration rule id")
    configured_parameters = {
        column.name for column in columns
        if isinstance(column, _ParameterColumn)
    }
    for rule in rules:
        target = rule.effect.parameter.name
        if target not in configured_parameters:
            raise ValueError(
                "DriveParameter target must also be a Param configuration column"
            )

    return _ConfiguredDesign(
        design,
        active,
        columns,
        tuple(normalized),
        rules,
    )


def _feature_prefix(root, source):
    """Resolve an authored source by object identity, never native ID guesses."""
    if root is source:
        return root
    if not isinstance(root, Shape) or not isinstance(root.data, tuple):
        return None
    if root.kind in ("union", "difference", "intersection"):
        original, added = root.data
        if added is source or (added.kind == "labeled" and added.data[0] is source):
            return root
        return _feature_prefix(original, source)
    if root.kind in (
        "fillet", "chamfer", "shell", "material_assignment", "appearance_assignment",
        "rectangular_pattern", "circular_pattern", "sheet_fold", "sheet_edge_flange",
        "sheet_hem", "sheet_path_flange", "sheet_perforate",
    ):
        return _feature_prefix(root.data[0], source)
    return None


def _row_variable(name):
    """Return one stable replay identity for an authored configuration row."""
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
    return f"$config_row_{digest}"


def _same_native_command(left, right):
    return (
        left.get("command") == right.get("command")
        and left.get("params", {}) == right.get("params", {})
    )


def _suppression_command_index(configured, name, commands, feature):
    """Find the exact compiled history command for one authored feature."""
    from .compiler import ModelError, _compile_model_commands

    if isinstance(configured.design, Shape):
        prefix = _feature_prefix(configured.design, feature)
        if prefix is None:
            raise ModelError(
                "suppression source must be an already-applied feature of this design"
            )
        prefix_commands = [
            c for c in _compile_model_commands(prefix, name)
            if c["command"] != "parameters.add"
        ]
        geometry_indexes = [
            i for i, c in enumerate(commands)
            if c["command"] != "parameters.add"
        ]
        if not prefix_commands or len(prefix_commands) > len(geometry_indexes):
            raise ModelError("suppression source has no native history feature")
        index = geometry_indexes[len(prefix_commands) - 1]
        actual = [commands[i] for i in geometry_indexes[:len(prefix_commands)]]
        if any(
            not _same_native_command(a, b)
            for a, b in zip(actual, prefix_commands)
        ):
            raise ModelError(
                "suppression source does not resolve to an exact history prefix"
            )
        return index

    from .assembly import (
        _as_assembly,
        _component_slug,
        _definition_names,
        _namespace_commands,
    )
    from .core import _shape_contains

    from .model_objects import _ComponentFeatureReference

    assembly = _as_assembly(configured.design)
    names = _definition_names(assembly)
    by_definition = {}
    for instance in assembly.instances:
        by_definition.setdefault(instance.definition.key, []).append(instance)

    matches = []
    referenced_definition = False
    for definition_number, (key, instances) in enumerate(
        by_definition.items(),
        start=1,
    ):
        definition = instances[0].definition
        source = feature
        if isinstance(feature, _ComponentFeatureReference):
            if key != feature.definition_key:
                continue
            referenced_definition = True
            try:
                source = dict(definition.features)[feature.name]
            except KeyError as exc:
                raise ModelError(
                    f"component definition has no exported feature {feature.name!r}"
                ) from exc
        elif not _shape_contains(definition.shape, source):
            continue

        prefix = _feature_prefix(definition.shape, source)
        if prefix is None:
            continue
        external_names = {
            parameter_name
            for parameter_name, _ in definition.external_parameters
        }
        prefix_commands = _namespace_commands(
            _compile_model_commands(prefix, _component_slug(names[key])),
            names[key],
            definition_number=definition_number,
            external_names=external_names,
        )
        prefix_geometry = [
            c for c in prefix_commands
            if c["command"] != "parameters.add"
        ]
        if not prefix_geometry:
            continue
        target = prefix_geometry[-1]
        matches.extend(
            index for index, command in enumerate(commands)
            if _same_native_command(command, target)
        )

    if isinstance(feature, _ComponentFeatureReference) and not referenced_definition:
        raise ModelError(
            "component feature reference is not part of this configured design"
        )

    matches = sorted(set(matches))
    if not matches:
        raise ModelError(
            "suppression source must be an already-applied feature of this design"
        )
    if len(matches) != 1:
        raise ModelError(
            "suppression source resolves ambiguously in the compiled assembly"
        )
    return matches[0]


def _configuration_commands(configured, name, commands):
    """Bind native configuration targets and append table authoring."""
    from .compiler import ModelError

    commands = [dict(command) for command in commands]
    parameter_names = {c["params"]["name"] for c in commands
                       if c["command"] == "parameters.add"}
    params = []
    features = []
    keys = []
    bound_indexes = set()

    def command(kind, **values):
        return {"command": kind, "params": values}

    for number, column in enumerate(configured.columns, start=1):
        if isinstance(column, _ParameterColumn):
            if column.name not in parameter_names:
                raise ModelError(f"unknown native configuration parameter: {column.name}")
            params.append(column.name)
            keys.append(f"param:{column.name}")
            continue
        index = _suppression_command_index(
            configured,
            name,
            commands,
            column.feature,
        )
        if not commands[index]["command"].startswith(("solid.", "sheet.")):
            raise ModelError("suppression source must end in one native solid or sheet feature")
        if index in bound_indexes:
            raise ModelError("duplicate native suppression feature")
        bound_indexes.add(index)
        # The command API addresses configuration feature columns by the
        # replay-returned native feature name. SolidCraft stores the resolved
        # feature id in the saved configuration table; callers never supply it.
        feature_name = f"$config_name_{number}"
        bindings = dict(commands[index].get("bind", {}))
        bindings[feature_name] = "name"
        commands[index]["bind"] = bindings
        features.append(feature_name)
        keys.append(f"suppress:{feature_name}")

    options = {}
    if params:
        options["params"] = params
    if features:
        options["features"] = features
    commands.append(command("config.configure", **options))

    def row_binding(variable, row_name):
        return {
            variable: {
                "field": "rows",
                "where": {"name": row_name},
                "select": "id",
            }
        }

    row_refs = {}
    first = configured.rows[0][0]
    if first != "Default":
        rename = command("config.row", name="Default", rename=first)
        variable = _row_variable(first)
        rename["bind"] = row_binding(variable, first)
        row_refs[first] = variable
        commands.append(rename)

    for row_number, (row, cells) in enumerate(configured.rows, start=1):
        update = command(
            "config.row",
            name=row,
            values=dict(zip(keys, cells)),
        )
        if row not in row_refs:
            variable = _row_variable(row)
            update["bind"] = row_binding(variable, row)
            row_refs[row] = variable
        commands.append(update)

    configured_parameter_names = {
        column.name for column in configured.columns
        if isinstance(column, _ParameterColumn)
    }
    for rule in configured.rules:
        target = rule.effect.parameter.name
        if target not in parameter_names:
            raise ModelError(
                f"unknown native configuration rule parameter: {target}"
            )
        if target not in configured_parameter_names:
            raise ModelError(
                f"configuration rule target is not a configured parameter: {target}"
            )
        missing_dependencies = [
            parameter.name
            for parameter in parameters_in(rule.effect.expression)
            if parameter.name not in parameter_names
        ]
        if missing_dependencies:
            raise ModelError(
                "unknown native configuration rule expression parameter: "
                + ", ".join(sorted(set(missing_dependencies)))
            )
        commands.append(
            command(
                "config.rule",
                rule={
                    "id": rule.id,
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "condition": {"type": "always"},
                    "effect": {
                        "type": "drive_parameter",
                        "parameter": target,
                        "expression": _configuration_expression(
                            rule.effect.expression
                        ),
                    },
                },
            )
        )

    commands.append(
        command("config.activate", row=row_refs[configured.active])
    )
    commands.append(command("config.table"))
    return commands

def _apply_configuration_document(configured, name, document):
    """Append generic configuration intent to an already compiled design."""
    from .replay import is_replay_document, replay_document

    commands = _configuration_commands(
        configured,
        name,
        document["commands"],
    )
    if is_replay_document(document):
        result = dict(document)
        result["commands"] = commands
        return result

    extras = {
        key: value for key, value in document.items()
        if key != "commands"
    }
    if any("bind" in command for command in commands):
        result = replay_document(commands)
        result.update(extras)
        return result
    return {"commands": commands, **extras}
