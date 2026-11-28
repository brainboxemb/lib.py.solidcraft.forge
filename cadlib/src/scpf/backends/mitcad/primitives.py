"""Mitcad lowering for primitive semantic IR."""
from __future__ import annotations

from math import isfinite

from ...compiler import ModelError, _require_positive
from ...core import (
    Expression,
    Parameter,
    Shape,
    _DirectionSelector,
    _dim_add,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    _sphere_center_from_anchor,
    command_value,
    number_text,
    parameters_in,
)
from ...ir import (
    AxisLineIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FeatureRefIR,
    FilletIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    SketchRelationsIR,
    SphereIR,
    SuppressionColumnIR,
    TranslationIR,
    _region_interior_point,
    normalize_shape,
    resolve_feature_ref,
)
from ...scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


from .sketch import _mitcad_offset_plane

FORMAT = "scpf-mitcad"
VERSION = 1

_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}


def _require_origin_plane(value, *, label):
    """Refuse axial placement that this Mitcad slice cannot preserve yet."""
    if parameters_in(value) or pv(value) != 0:
        raise ModelError(
            f"Mitcad {label} placement currently requires its axial "
            "coordinate on the origin plane"
        )


def _box_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, BoxIR):
        raise TypeError("Mitcad box lowering requires PlacementIR(BoxIR)")

    _require_positive(primitive.length, "box length")
    _require_positive(primitive.width, "box width")
    height = _require_positive(primitive.height, "box height")

    if node.anchor == (0, 0, -1):
        _require_origin_plane(node.point[2], label="Box")
        symmetric = False
    elif node.anchor == (0, 0, 0):
        axial = pv(node.point[2])
        if parameters_in(node.point[2]):
            raise ModelError(
                "Mitcad Box axial placement currently requires a numeric "
                "origin-plane equivalent"
            )
        if abs(axial) <= 1e-9:
            symmetric = True
        elif not parameters_in(primitive.height) and abs(axial - height / 2.0) <= 1e-9:
            # A centered Forge box whose bottom lies on XY is the same native
            # solid as a one-sided Mitcad box starting on XY.
            symmetric = False
        else:
            raise ModelError(
                "Mitcad Box placement currently requires its center on XY "
                "or its bottom face on XY"
            )
    else:
        raise ModelError(
            "Mitcad Box placement currently supports Anchor.BOTTOM or "
            "Anchor.CENTER only"
        )

    corner = _box_corner_from_anchor(
        primitive.length,
        primitive.width,
        primitive.height,
        node.point,
        _DirectionSelector(node.anchor),
    )

    definition = {
        "type": "box",
        "plane": "xy",
        "corner": [
            command_value(corner[0]),
            command_value(corner[1]),
        ],
        "length": command_value(primitive.length),
        "width": command_value(primitive.width),
        "height": command_value(primitive.height),
        "symmetric": symmetric,
        "operation": operation,
        "participants": [],
    }
    return {
        "cmd": "add_feature",
        "name": name,
        "def": definition,
    }


_CYLINDER_PLANES = {
    "X": ("yz", (-1, 0, 0), 0),
    "Y": ("xz", (0, -1, 0), 1),
    "Z": ("xy", (0, 0, -1), 2),
}


def _cylinder_plane_center(axis, point):
    if axis == "X":
        # Mitcad YZ plane coordinates: u=-Z, v=+Y.
        return (-point[2], point[1])
    if axis == "Y":
        # Mitcad XZ plane coordinates: u=+X, v=-Z.
        return (point[0], -point[2])
    if axis == "Z":
        return (point[0], point[1])
    raise ModelError(
        f"Mitcad Cylinder IR requires a principal axis, got {axis!r}"
    )


def _cylinder_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, CylinderIR):
        raise TypeError(
            "Mitcad cylinder lowering requires PlacementIR(CylinderIR)"
        )

    _require_positive(primitive.height, "cylinder height")
    _require_positive(primitive.diameter, "cylinder diameter")
    try:
        plane, axial_start, axial_index = _CYLINDER_PLANES[primitive.axis]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad Cylinder IR requires a principal axis, "
            f"got {primitive.axis!r}"
        ) from exc

    _require_origin_plane(
        node.point[axial_index],
        label="Cylinder",
    )
    if node.anchor not in ((0, 0, 0), axial_start):
        raise ModelError(
            "Mitcad Cylinder placement currently supports CENTER or the "
            "negative axial end anchor only"
        )

    center = _cylinder_plane_center(primitive.axis, node.point)
    return {
        "cmd": "add_feature",
        "name": name,
        "def": {
            "type": "cylinder",
            "plane": plane,
            "center": [
                command_value(center[0]),
                command_value(center[1]),
            ],
            "diameter": command_value(primitive.diameter),
            "height": command_value(primitive.height),
            "symmetric": node.anchor == (0, 0, 0),
            "operation": operation,
            "participants": [],
        },
    }


def _cone_commands(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
    plane_binding: str = "cone_plane",
) -> list[dict]:
    """Lower semantic Cone placement through a principal support plane."""
    primitive = node.primitive
    if not isinstance(primitive, ConeIR):
        raise TypeError("Mitcad cone lowering requires PlacementIR(ConeIR)")

    _require_positive(primitive.height, "cone height")
    _require_positive(primitive.diameter, "cone diameter")
    if pv(primitive.top_diameter) < 0:
        raise ModelError("cone top diameter must be zero or positive")

    try:
        plane, _axial_start, axial_index = _CYLINDER_PLANES[primitive.axis]
    except KeyError as exc:
        raise ModelError(
            f"Mitcad ConeIR requires a principal axis, got {primitive.axis!r}"
        ) from exc

    selector = _DirectionSelector(node.anchor)
    try:
        base = _cone_base_from_anchor(
            primitive.height,
            primitive.axis,
            node.point,
            selector,
        )
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    plane_commands, native_plane = _mitcad_offset_plane(
        plane.upper(),
        base[axial_index],
        label="Cone",
        binding=plane_binding,
    )
    center = _cylinder_plane_center(primitive.axis, base)

    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "name": name,
            "def": {
                "type": "cone",
                "plane": native_plane,
                "center": [
                    command_value(center[0]),
                    command_value(center[1]),
                ],
                "radius": command_value(primitive.diameter / 2),
                "top_radius": command_value(primitive.top_diameter / 2),
                "height": command_value(primitive.height),
                "symmetric": False,
                "operation": operation,
                "participants": [],
            },
        },
    ]


def _sphere_center(node: PlacementIR):
    """Derive semantic Sphere centre from PlacementIR before native transport."""
    primitive = node.primitive
    if not isinstance(primitive, SphereIR):
        raise TypeError("Mitcad sphere lowering requires PlacementIR(SphereIR)")
    _require_positive(primitive.radius, "sphere radius")
    return _sphere_center_from_anchor(
        primitive.radius,
        node.point,
        _DirectionSelector(node.anchor),
    )


def _sphere_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
) -> dict:
    """Lower the already-qualified origin-plane Sphere CSG spelling."""
    primitive = node.primitive
    center = _sphere_center(node)
    _require_origin_plane(center[2], label="Sphere CSG")
    return {
        "cmd": "add_feature",
        "name": name,
        "def": {
            "type": "sphere",
            "plane": "xy",
            "center": [
                command_value(center[0]),
                command_value(center[1]),
            ],
            "diameter": command_value(primitive.radius * 2),
            "operation": operation,
            "participants": [],
        },
    }


def _sphere_commands(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new_body",
    plane_binding: str = "sphere_plane",
) -> list[dict]:
    """Lower Sphere placement with backend-owned support geometry."""
    primitive = node.primitive
    center = _sphere_center(node)
    plane_commands, native_plane = _mitcad_offset_plane(
        "XY",
        center[2],
        label="Sphere",
        binding=plane_binding,
    )
    return [
        *plane_commands,
        {
            "cmd": "add_feature",
            "name": name,
            "def": {
                "type": "sphere",
                "plane": native_plane,
                "center": [
                    command_value(center[0]),
                    command_value(center[1]),
                ],
                "diameter": command_value(primitive.radius * 2),
                "operation": operation,
                "participants": [],
            },
        },
    ]


def _csg_helper_binding(path: tuple[str, ...]) -> str:
    """Return one deterministic backend-private binding for semantic CSG path."""
    return "csg_plane_" + "_".join(path)


def _csg_primitive_commands(
    node: PlacementIR,
    name: str,
    operation: str,
    *,
    path: tuple[str, ...],
) -> tuple[list[dict], int]:
    """Lower one semantic primitive to native helpers + one feature command.

    The returned index is relative to this command group and identifies the
    native command representing the semantic Forge feature. Private helper
    commands before it are never semantic history entries.
    """
    if isinstance(node.primitive, BoxIR):
        return [_box_command(node, name, operation=operation)], 0
    if isinstance(node.primitive, CylinderIR):
        return [_cylinder_command(node, name, operation=operation)], 0
    if isinstance(node.primitive, ConeIR):
        commands = _cone_commands(
            node,
            name,
            operation=operation,
            plane_binding=_csg_helper_binding(path),
        )
        return commands, len(commands) - 1
    if isinstance(node.primitive, SphereIR):
        commands = _sphere_commands(
            node,
            name,
            operation=operation,
            plane_binding=_csg_helper_binding(path),
        )
        return commands, len(commands) - 1
    raise ModelError(
        "Mitcad primitive CSG does not support "
        f"{type(node.primitive).__name__}"
    )
