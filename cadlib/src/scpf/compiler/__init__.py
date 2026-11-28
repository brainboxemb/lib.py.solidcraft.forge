"""Stable compiler facade over Forge semantic IR and native backends."""
from ..core import Shape
from .errors import ModelError, require_positive, _require_positive
from .legacy import (
    _command,
    _param_commands,
    _collect,
    _compile_model_commands,
    compile_shape_legacy_with_dependencies,
    _compile_shape_legacy_with_dependencies,
)
from .dispatch import compile_model_with_dependencies, _compile_model_with_dependencies


def compile_model(shape: Shape, name: str) -> dict:
    """Compile one Shape through Forge semantic IR to SolidCraft commands."""
    return compile_model_with_dependencies(shape, name)[0]


__all__ = ["ModelError", "compile_model"]
