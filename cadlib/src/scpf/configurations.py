"""Document-level native SolidCraft configuration-table intent and lowering."""

from dataclasses import dataclass
from math import isfinite

from .core import Parameter, Shape, number_text


@dataclass(frozen=True)
class _ParameterColumn:
    name: str


@dataclass(frozen=True)
class _SuppressionColumn:
    feature: Shape


@dataclass(frozen=True)
class _ConfiguredDesign:
    geometry: object
    active: str
    columns: tuple
    rows: tuple


def Param(name):
    """Select an existing native model parameter as a configuration column."""
    if isinstance(name, Parameter):
        name = name.name
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError("Param requires a native parameter name")
    return _ParameterColumn(name)


def Suppress(feature):
    """Select the exact applied Forge feature Shape as a suppression column."""
    if not isinstance(feature, Shape):
        raise TypeError("Suppress requires an authored feature Shape")
    return _SuppressionColumn(feature)


def Configure(geometry, *, active, columns, rows):
    """Return one final design with an editable native configuration table.

    Each row contains one parameter expression or suppression boolean per
    column, in column order. The active name must be one of the declared rows.
    """
    if not isinstance(geometry, Shape):
        raise TypeError("configuration authoring currently requires a final Shape")
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
    return _ConfiguredDesign(geometry, active, columns, tuple(normalized))


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


def _configuration_commands(configured, name, commands):
    """Bind actual native feature IDs and append native table authoring."""
    from .compiler import ModelError, _compile_model_commands

    commands = [dict(command) for command in commands]
    parameter_names = {c["params"]["name"] for c in commands
                       if c["command"] == "parameters.add"}
    geometry_indexes = [i for i, c in enumerate(commands)
                        if c["command"] != "parameters.add"]
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
        prefix = _feature_prefix(configured.geometry, column.feature)
        if prefix is None:
            raise ModelError("suppression source must be an already-applied feature of this design")
        prefix_commands = [c for c in _compile_model_commands(prefix, name)
                           if c["command"] != "parameters.add"]
        if not prefix_commands or len(prefix_commands) > len(geometry_indexes):
            raise ModelError("suppression source has no native history feature")
        index = geometry_indexes[len(prefix_commands) - 1]
        actual = [commands[i] for i in geometry_indexes[:len(prefix_commands)]]
        if any(a["command"] != b["command"] or a["params"] != b["params"]
               for a, b in zip(actual, prefix_commands)):
            raise ModelError("suppression source does not resolve to an exact history prefix")
        if not commands[index]["command"].startswith(("solid.", "sheet.")):
            raise ModelError("suppression source must end in one native solid or sheet feature")
        if index in bound_indexes:
            raise ModelError("duplicate native suppression feature")
        bound_indexes.add(index)
        feature_id = f"$config_feature_{number}"
        feature_name = f"$config_name_{number}"
        bindings = dict(commands[index].get("bind", {}))
        bindings[feature_id] = "feature"
        bindings[feature_name] = "name"
        commands[index]["bind"] = bindings
        features.append(feature_name)
        keys.append(f"suppress:{feature_id}")

    options = {}
    if params:
        options["params"] = params
    if features:
        options["features"] = features
    commands.append(command("config.configure", **options))
    first = configured.rows[0][0]
    if first != "Default":
        commands.append(command("config.row", name="Default", rename=first))
    for row, cells in configured.rows:
        commands.append(command("config.row", name=row, values=dict(zip(keys, cells))))
    commands.append(command("config.activate", row=configured.active))
    commands.append(command("config.table"))
    return commands
