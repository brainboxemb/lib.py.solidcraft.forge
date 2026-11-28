"""Private compatibility lowering for not-yet-typed SolidCraft surface."""
from ..core import (
    Shape,
    Parameter,
    number_text,
    parameters_in,
    _native_dependencies,
    _plain_command_value,
)
from ..replay import replay_document
from .errors import ModelError


def _command(command_name, **params):
    return {"command": command_name, "params": params}


def _param_commands(params, *, units=None):
    units = units or {}
    return [
        _command(
            "parameters.add",
            name=p.name,
            expression=number_text(p.value),
            unit=units.get(p.name, "mm"),
        )
        for p in params
    ]


def _collect(node, values=None):
    """Collect named parameters in first-use order, rejecting conflicts."""
    if values is None:
        values = {}
    if isinstance(node, Shape):
        _collect(node.data, values)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _collect(item, values)
    else:
        for param in parameters_in(node):
            previous = values.setdefault(param.name, param.value)
            if previous != param.value:
                raise ModelError(f"conflicting values for parameter {param.name}")
    return tuple(Parameter(k, v) for k, v in values.items())


def _compile_model_commands(shape: Shape, name: str) -> list[dict]:
    """Compile one Shape while retaining typed native expression markers."""
    if not isinstance(shape, Shape):
        raise TypeError("the final script expression must produce a Shape")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")
    from ..features import _is_feature_tree, compile_features
    from ..csg import _csg_new
    return (
        compile_features(shape, name)
        if _is_feature_tree(shape)
        else _param_commands(_collect(shape)) + _csg_new(shape, name)
    )


def compile_shape_legacy_with_dependencies(shape: Shape, name: str):
    """Compile one not-yet-migrated Shape through stable legacy lowering."""
    from ..configurations import _configuration_commands

    commands = _compile_model_commands(shape, name)
    configuration = getattr(shape, "_configuration", None)
    if configuration is not None:
        commands = _configuration_commands(shape, configuration, name, commands)
    plain_commands = _plain_command_value(commands)
    document = (
        replay_document(plain_commands)
        if any("bind" in command for command in plain_commands)
        else {"commands": plain_commands}
    )
    return document, _native_dependencies(commands)


_compile_shape_legacy_with_dependencies = compile_shape_legacy_with_dependencies
