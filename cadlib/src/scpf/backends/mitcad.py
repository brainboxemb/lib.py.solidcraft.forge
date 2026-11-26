"""Lower the first portable SCPF intent to native Mitcad commands.

This is deliberately small. The #192 feasibility spike proves that Forge model
intent can reach a second native CAD engine without translating through
SolidCraft commands or weakening the public SCPF model source.
"""

from __future__ import annotations

from ..compiler import ModelError, _collect, _require_positive
from ..core import (
    Anchor,
    Shape,
    _box_corner_from_anchor,
    _native_dependencies,
    _plain_command_value,
    command_value,
)


FORMAT = "scpf-mitcad"
VERSION = 1


def _parameter_commands(shape: Shape) -> list[dict]:
    """Publish Forge model parameters as native Mitcad user parameters."""
    return [
        {
            "cmd": "add_parameter",
            "name": parameter.name,
            "value": parameter.value,
            "unit": "mm",
        }
        for parameter in _collect(shape)
    ]


def _box_command(shape: Shape, name: str) -> dict:
    length, width, height, anchor = shape.data
    _require_positive(length, "box length")
    _require_positive(width, "box width")
    _require_positive(height, "box height")

    anchor_vector = tuple(anchor.vector)
    if anchor_vector not in ((0, 0, -1), (0, 0, 0)):
        raise ModelError(
            "Mitcad Box lowering currently supports Anchor.BOTTOM or "
            "Anchor.CENTER only"
        )

    corner = _box_corner_from_anchor(
        length,
        width,
        height,
        (0, 0, 0),
        anchor,
    )

    definition = {
        "type": "box",
        "plane": "xy",
        "corner": [
            command_value(corner[0]),
            command_value(corner[1]),
        ],
        "length": command_value(length),
        "width": command_value(width),
        "height": command_value(height),
        "symmetric": anchor_vector == (0, 0, 0),
        "operation": "new_body",
        "participants": [],
    }
    return {
        "cmd": "add_feature",
        "name": name,
        "def": definition,
    }


def compile_model_with_dependencies(shape: Shape, name: str):
    """Compile one supported Forge Shape directly to Mitcad native intent."""
    if not isinstance(shape, Shape):
        raise TypeError("the final script expression must produce a Shape")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if shape.kind != "box":
        raise ModelError(
            f"Mitcad backend does not yet support Forge shape kind "
            f"{shape.kind!r}; #192 intentionally fails unsupported intent"
        )

    commands = [
        *_parameter_commands(shape),
        _box_command(shape, name),
    ]
    dependencies = _native_dependencies(commands)
    return {
        "format": FORMAT,
        "version": VERSION,
        "backend": "mitcad",
        "commands": _plain_command_value(commands),
    }, dependencies


def compile_model(shape: Shape, name: str) -> dict:
    """Compile the supported portable Forge subset to Mitcad commands."""
    return compile_model_with_dependencies(shape, name)[0]


__all__ = [
    "FORMAT",
    "VERSION",
    "compile_model",
    "compile_model_with_dependencies",
]
