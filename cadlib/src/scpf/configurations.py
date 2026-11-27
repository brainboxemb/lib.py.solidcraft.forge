"""Final-model configuration intent and SolidCraft lowering."""

from dataclasses import dataclass
import hashlib
from math import isfinite
import re

from .core import Parameter, Shape, _FeatureHandle, number_text


@dataclass(frozen=True)
class _ParameterColumn:
    name: str


@dataclass(frozen=True)
class _SuppressionColumn:
    feature: object


@dataclass(frozen=True)
class _Configuration:
    active: str
    columns: tuple
    rows: tuple


def _configuration_column(value):
    """Normalize one public configuration target to private typed metadata."""
    if isinstance(value, Parameter):
        return _ParameterColumn(value.name)

    from .model_objects import _ComponentFeatureReference
    if isinstance(value, _FeatureHandle):
        return _SuppressionColumn(value.shape)
    if isinstance(value, (Shape, _ComponentFeatureReference)):
        return _SuppressionColumn(value)

    raise TypeError(
        "configuration columns must contain Parameter or authored feature handles"
    )


_PARAMETER_LITERAL = re.compile(
    r"^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?"
    r"(?:\\s+[A-Za-z°%][A-Za-z0-9_°%/*^.-]*)?$"
)


def _parameter_cell_value(cell):
    """Normalize one concrete configuration parameter value.

    Configuration rows select values. They do not author new relationships
    between model parameters; those relationships belong in normal Forge model
    expressions outside the configuration table.
    """
    if (
        isinstance(cell, (int, float))
        and not isinstance(cell, bool)
        and isfinite(cell)
    ):
        return number_text(cell)

    if isinstance(cell, str):
        text = cell.strip()
        if text and _PARAMETER_LITERAL.fullmatch(text):
            return text
        raise ValueError(
            "configuration parameter cells must be literal values; "
            "parameter coupling expressions are not supported"
        )

    raise TypeError(
        "configuration parameter cells require a finite number or unit-bearing literal"
    )


def _configure_model(design, *, active, columns, rows):
    """Attach one configuration definition to an already-built final model."""
    from .model_objects import Assembly, ModelInstance

    if not isinstance(design, (Shape, ModelInstance, Assembly)):
        raise TypeError(
            "configure() requires a final Shape, component occurrence or Assembly"
        )
    if getattr(design, "_configuration", None) is not None:
        raise ValueError("final model already has a configuration")

    try:
        columns = tuple(columns)
    except TypeError as exc:
        raise TypeError("configuration columns must be iterable") from exc
    if not columns:
        raise ValueError("configure() requires at least one column")

    normalized_columns = tuple(_configuration_column(value) for value in columns)
    keys = [
        ("param", column.name)
        if isinstance(column, _ParameterColumn)
        else ("feature", id(column.feature))
        for column in normalized_columns
    ]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate configuration column")

    if not isinstance(rows, dict) or not rows:
        raise ValueError("configure() requires an ordered mapping of named rows")

    normalized_rows = []
    for name, cells in rows.items():
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError("configuration row names must be non-empty text")
        try:
            cells = tuple(cells)
        except TypeError as exc:
            raise TypeError(
                f"configuration {name!r} cells must be iterable"
            ) from exc
        if len(cells) != len(normalized_columns):
            raise ValueError(f"configuration {name!r} has the wrong cell count")

        converted = []
        for column, cell in zip(normalized_columns, cells):
            if isinstance(column, _SuppressionColumn):
                if not isinstance(cell, bool):
                    raise TypeError("suppression cells must be bool")
                converted.append("true" if cell else "false")
            else:
                converted.append(_parameter_cell_value(cell))
        normalized_rows.append((name, tuple(converted)))

    if active not in rows:
        raise ValueError("active configuration must name a declared row")

    configuration = _Configuration(
        active=active,
        columns=normalized_columns,
        rows=tuple(normalized_rows),
    )
    object.__setattr__(design, "_configuration", configuration)
    return design


def _feature_prefix(root, source):
    """Resolve an authored source by object identity, never native ID guesses."""
    if root is source:
        return root
    if not isinstance(root, Shape) or not isinstance(root.data, tuple):
        return None
    if root.kind in ("union", "difference", "intersection"):
        original, added = root.data
        if added is source or (
            isinstance(added, Shape)
            and added.kind == "labeled"
            and added.data[0] is source
        ):
            return root
        return _feature_prefix(original, source)
    if root.kind in (
        "exported_feature",
        "named_feature",
        "fillet",
        "chamfer",
        "shell",
        "material_assignment",
        "appearance_assignment",
        "rectangular_pattern",
        "circular_pattern",
        "sheet_fold",
        "sheet_edge_flange",
        "sheet_hem",
        "sheet_path_flange",
        "sheet_perforate",
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


def _suppression_command_index(design, name, commands, feature):
    """Find the exact compiled history command for one authored feature."""
    from .compiler import ModelError, _compile_model_commands

    if isinstance(design, Shape):
        prefix = _feature_prefix(design, feature)
        if prefix is None:
            raise ModelError(
                "suppression source must be an already-applied feature of this design"
            )
        prefix_commands = [
            command
            for command in _compile_model_commands(prefix, name)
            if command["command"] != "parameters.add"
        ]
        geometry_indexes = [
            index
            for index, command in enumerate(commands)
            if command["command"] != "parameters.add"
        ]
        if not prefix_commands or len(prefix_commands) > len(geometry_indexes):
            raise ModelError("suppression source has no native history feature")
        actual = [
            commands[item]
            for item in geometry_indexes[:len(prefix_commands)]
        ]
        if any(
            not _same_native_command(actual_command, prefix_command)
            for actual_command, prefix_command in zip(actual, prefix_commands)
        ):
            raise ModelError(
                "suppression source does not resolve to an exact history prefix"
            )
        target_offsets = [
            offset
            for offset, command in enumerate(prefix_commands)
            if command["command"].startswith(("solid.", "sheet."))
        ]
        if not target_offsets:
            raise ModelError("suppression source has no native history feature")
        return geometry_indexes[target_offsets[-1]]

    from .assembly import (
        _as_assembly,
        _component_slug,
        _definition_names,
        _namespace_commands,
    )
    from .core import _shape_contains
    from .model_objects import _ComponentFeatureReference

    assembly = _as_assembly(design)
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
            command
            for command in prefix_commands
            if command["command"] != "parameters.add"
        ]
        targets = [
            command
            for command in prefix_geometry
            if command["command"].startswith(("solid.", "sheet."))
        ]
        if not targets:
            continue
        target = targets[-1]
        matches.extend(
            index
            for index, command in enumerate(commands)
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


def _configuration_commands(design, configuration, name, commands):
    """Bind configuration targets and append native table authoring."""
    from .compiler import ModelError

    commands = [dict(command) for command in commands]
    parameter_names = {
        command["params"]["name"]
        for command in commands
        if command["command"] == "parameters.add"
    }
    params = []
    features = []
    keys = []
    bound_indexes = set()

    def command(kind, **values):
        return {"command": kind, "params": values}

    for number, column in enumerate(configuration.columns, start=1):
        if isinstance(column, _ParameterColumn):
            if column.name not in parameter_names:
                raise ModelError(
                    f"unknown native configuration parameter: {column.name}"
                )
            params.append(column.name)
            keys.append(f"param:{column.name}")
            continue

        index = _suppression_command_index(
            design,
            name,
            commands,
            column.feature,
        )
        if not commands[index]["command"].startswith(("solid.", "sheet.")):
            raise ModelError(
                "suppression source must end in one native solid or sheet feature"
            )
        if index in bound_indexes:
            raise ModelError("duplicate native suppression feature")
        bound_indexes.add(index)

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
    first = configuration.rows[0][0]
    if first != "Default":
        rename = command("config.row", name="Default", rename=first)
        variable = _row_variable(first)
        rename["bind"] = row_binding(variable, first)
        row_refs[first] = variable
        commands.append(rename)

    for row, cells in configuration.rows:
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

    commands.append(
        command("config.activate", row=row_refs[configuration.active])
    )
    commands.append(command("config.table"))
    return commands
