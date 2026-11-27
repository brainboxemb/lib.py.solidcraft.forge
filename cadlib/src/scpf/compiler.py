"""Stable SolidCraft compiler API over Forge semantic IR.

Public callers still pass Forge Shape values. They are normalized to the same
engine-neutral semantic IR used by other native backends before SolidCraft
lowering begins. The legacy command compiler remains private transition support
for stable Forge surface that has not yet migrated to typed IR nodes.
"""
from math import isfinite

from .core import (
    Shape, Parameter, number_text, parameters_in, _pv as pv,
    _native_dependencies, _plain_command_value,
)
from .replay import replay_document


class ModelError(ValueError):
    """Report unsupported or invalid CAD model intent.

    Use when:
        Catch Forge compilation/model validation failures separately from normal
        Python argument errors when integrating the lower-level compiler API.

    Limits:
        User model code normally fixes the underlying model instead of handling
        this exception as a recoverable geometry result.
    """


def _require_positive(value, label):
    num = pv(value)
    if not isfinite(num) or num <= 0:
        raise ModelError(f"{label} must be positive")
    return num


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
    from .features import _is_feature_tree, compile_features
    from .csg import _csg_new
    return (
        compile_features(shape, name)
        if _is_feature_tree(shape)
        else _param_commands(_collect(shape)) + _csg_new(shape, name)
    )


def _compile_shape_legacy_with_dependencies(shape: Shape, name: str):
    """Compile one not-yet-migrated Shape through the stable legacy lowering."""
    from .configurations import _configuration_commands

    commands = _compile_model_commands(shape, name)
    configuration = getattr(shape, "_configuration", None)
    if configuration is not None:
        commands = _configuration_commands(
            shape,
            configuration,
            name,
            commands,
        )
    plain_commands = _plain_command_value(commands)
    document = (
        replay_document(plain_commands)
        if any("bind" in command for command in plain_commands)
        else {"commands": plain_commands}
    )
    return document, _native_dependencies(commands)


def _compile_model_with_dependencies(shape: Shape, name: str):
    """Compile stable SolidCraft product intent through the IR boundary.

    Geometry Shapes normalize to ModelIR. Configure(...) remains a
    SolidCraft-only document-level wrapper until configuration semantics gain
    their own portable IR boundary, so it deliberately uses the stable legacy
    lowering that already owns native configuration-table authoring.
    """
    from .configurations import _ConfiguredDesign
    if isinstance(shape, _ConfiguredDesign):
        return _compile_shape_legacy_with_dependencies(shape, name)

    from .backends.solidcraft import compile_ir_with_dependencies
    from .ir import normalize_shape
    return compile_ir_with_dependencies(normalize_shape(shape), name)


def compile_model(shape: Shape, name: str) -> dict:
    """Compile one Shape through Forge semantic IR to SolidCraft commands.

    Parameters:
        shape: Final Shape tree to compile.
        name: Model/body name used for generated SolidCraft commands. It must be a valid identifier.

    Use when:
        Lower-level tooling already has a final Shape object and needs the JSON
        command plan without executing a model source file.

    Limits:
        The final value must be a Shape. Normal user workflows usually call the
        scpf runner/CLI instead.

    Example:
        document = compile_model(Box(80, 50, 12), "Panel")
    """
    return _compile_model_with_dependencies(shape, name)[0]
