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


def _sketch_extrusion_commands(shape: Shape, name: str) -> list[dict]:
    (
        sketch_name,
        plane,
        origin,
        plane_offset,
        profiles,
        distance,
        direction,
        operations,
        profile_picks,
        exact_regions,
        rotation,
    ) = shape.data

    if plane not in ("XY", "XZ", "YZ"):
        raise ModelError("Mitcad standalone Sketch requires XY, XZ or YZ")
    if origin is not None or plane_offset is not None or rotation is not None:
        raise ModelError(
            "Mitcad standalone Sketch frame/offset is not qualified yet"
        )
    if operations:
        raise ModelError(
            "Mitcad Sketch pattern/mirror lowering is not qualified yet"
        )
    if profile_picks is not None or exact_regions:
        raise ModelError(
            "Mitcad selective Sketch profile lowering is not qualified yet"
        )
    if len(profiles) != 1:
        raise ModelError(
            "Mitcad standalone Sketch extrusion currently requires "
            "exactly one profile"
        )

    profile, profile_anchor, offset = profiles[0]
    if profile.kind != "circle":
        raise ModelError(
            "Mitcad standalone Sketch extrusion currently supports "
            "Circle2D only"
        )
    if profile_anchor is not Anchor.CENTER:
        raise ModelError(
            "Mitcad Circle2D extrusion currently requires Anchor.CENTER"
        )
    if tuple(command_value(value) for value in offset) != (0, 0):
        raise ModelError(
            "Mitcad Circle2D extrusion offset is not qualified yet"
        )
    if direction == "symmetric":
        raise ModelError(
            "Mitcad symmetric Sketch extrusion is not qualified yet"
        )
    if direction not in ("positive", "negative"):
        raise ModelError(
            f"Mitcad Sketch extrusion direction is unsupported: {direction!r}"
        )

    (diameter,) = profile.data
    _require_positive(diameter, "circle diameter")
    _require_positive(distance, "sketch extrusion distance")

    radius = diameter / 2
    extent_distance = command_value(distance)
    if direction == "negative":
        extent_distance = f"-({extent_distance})"

    sketch_definition = {
        "type": "sketch",
        "plane": plane.lower(),
        "entities": [
            {
                "id": "p1",
                "type": "point",
                "at": [0, 0],
                "fixed": True,
            },
            {
                "id": "c1",
                "type": "circle",
                "center": "p1",
                "radius": command_value(radius),
            },
        ],
        "constraints": [],
        "dimensions": [],
    }
    extrude_definition = {
        "type": "extrude",
        "profiles": [
            {
                "sketch": sketch_name,
                "region": "r{c1}",
            }
        ],
        "extent": {
            "type": "distance",
            "distance": extent_distance,
        },
        "flip": False,
        "operation": "new_body",
        "participants": [],
    }
    return [
        {
            "cmd": "add_feature",
            "name": sketch_name,
            "def": sketch_definition,
        },
        {
            "cmd": "add_feature",
            "name": name,
            "def": extrude_definition,
        },
    ]


def compile_model_with_dependencies(shape: Shape, name: str):
    """Compile one supported Forge Shape directly to Mitcad native intent."""
    if not isinstance(shape, Shape):
        raise TypeError("the final script expression must produce a Shape")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if shape.kind == "box":
        geometry_commands = [_box_command(shape, name)]
    elif shape.kind == "sketch_base_extrusion":
        geometry_commands = _sketch_extrusion_commands(shape, name)
    else:
        raise ModelError(
            f"Mitcad backend does not yet support Forge shape kind "
            f"{shape.kind!r}; #192 intentionally fails unsupported intent"
        )

    commands = [
        *_parameter_commands(shape),
        *geometry_commands,
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
