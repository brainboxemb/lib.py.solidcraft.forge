"""Lower typed Forge semantic IR to native SolidCraft commands.

Portable IR nodes are lowered directly here. LegacyShapeIR is the explicit
transition boundary for stable Forge functionality that has not yet migrated
to typed semantic IR.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
from math import isfinite

from ..compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from ..core import (
    Expression,
    Parameter,
    _DirectionSelector,
    _dim_abs,
    _dim_sub,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _cylinder_base_from_anchor,
    _primitive_center_from_anchor,
    _sphere_center_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    command_value,
    half,
    midpoint,
    number_text,
    parameters_in,
)
from ..ir import (
    AxisLineIR,
    BodyIR,
    BossFeatureIR,
    BoundOffsetIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CircularPatternIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    DirectionPairEdgeSetIR,
    ExplicitEdgePicksIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FeaturePlacementIR,
    FeatureRefIR,
    FilletIR,
    HoleIR,
    LipFeatureIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PlasticFeatureIR,
    PolygonProfileIR,
    ProfileEdgeSetIR,
    RegionIR,
    RectangleProfileIR,
    RectangularPatternIR,
    RevolveIR,
    RoundedRectangleProfileIR,
    SketchRelationsIR,
    SketchIR,
    SketchSupportIR,
    SketchChainIR,
    SketchEntityGraphIR,
    SketchEntityRefIR,
    SketchMirrorIR,
    SketchRectangularPatternIR,
    TextEntityIR,
    SheetBaseIR,
    SheetContourFlangeIR,
    SheetEdgeFlangeIR,
    SheetFoldIR,
    SheetHemIR,
    SheetPathFlangeIR,
    SheetPerforateIR,
    SheetRuleIR,
    ShellIR,
    SlotProfileIR,
    SnapFitFeatureIR,
    SphereIR,
    RestFeatureIR,
    SuppressionColumnIR,
    _region_interior_point,
    resolve_feature_ref,
)
from ..placement import _combine
from ..replay import replay_document
from ..scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}


def _require_positive(value, label):
    number = pv(value)
    if not isfinite(number) or number <= 0:
        raise ModelError(f"{label} must be positive")
    return number


def _command(command_name, **params):
    return {"command": command_name, "params": params}


def _parameter_commands(model: ModelIR) -> list[dict]:
    return [
        _command(
            "parameters.add",
            name=parameter.name,
            expression=number_text(parameter.value),
            unit=parameter.unit,
        )
        for parameter in model.parameters
    ]


def _role_scalar_expression_text(
    model: ModelIR,
    node,
    role: str,
    *,
    scalar_literal: bool = False,
) -> str:
    """Render bounded semantic scalar IR for one typed SolidCraft use site."""
    unit = {
        "length": "mm",
        "angle": "deg",
        "count": "",
        "ratio": "",
    }.get(role)
    if unit is None:
        raise ModelError(f"unsupported Forge parameter role {role!r}")
    parameters = {parameter.name: parameter for parameter in model.parameters}

    if isinstance(node, ScalarLiteralIR):
        text = number_text(node.value)
        if scalar_literal or not unit:
            return text
        return f"{text} {unit}"

    if isinstance(node, ScalarParameterRefIR):
        parameter = parameters.get(node.name)
        if parameter is None:
            raise ModelError(
                f"semantic scalar expression references unknown parameter {node.name!r}"
            )
        if role not in parameter.roles:
            raise ModelError(
                f"parameter {node.name!r} has no semantic {role} role"
            )
        if len(parameter.roles) > 1:
            return (
                f"{node.name} * 1 {unit}"
                if unit
                else f"{node.name} * 1"
            )
        return node.name

    if isinstance(node, ScalarUnaryIR):
        if node.operation != "negate":
            raise ModelError(
                f"unsupported scalar unary operation {node.operation!r}"
            )
        return (
            f"-({_role_scalar_expression_text(model, node.operand, role)})"
        )

    if not isinstance(node, ScalarBinaryIR):
        raise ModelError("typed scalar expression has unsupported IR node")

    if node.operation in {"add", "subtract"}:
        operator = "+" if node.operation == "add" else "-"
        return (
            f"({_role_scalar_expression_text(model, node.left, role)}) "
            f"{operator} "
            f"({_role_scalar_expression_text(model, node.right, role)})"
        )

    if node.operation == "multiply":
        if isinstance(node.left, ScalarLiteralIR):
            return (
                f"{_role_scalar_expression_text(model, node.left, role, scalar_literal=True)} "
                f"* ({_role_scalar_expression_text(model, node.right, role)})"
            )
        if isinstance(node.right, ScalarLiteralIR):
            return (
                f"({_role_scalar_expression_text(model, node.left, role)}) * "
                f"{_role_scalar_expression_text(model, node.right, role, scalar_literal=True)}"
            )

    if (
        node.operation == "divide"
        and isinstance(node.right, ScalarLiteralIR)
        and node.right.value != 0
    ):
        return (
            f"({_role_scalar_expression_text(model, node.left, role)}) / "
            f"{_role_scalar_expression_text(model, node.right, role, scalar_literal=True)}"
        )

    raise ModelError(
        "typed scalar expression requires affine numeric scaling"
    )


def _role_command_value(model: ModelIR, value, role: str):
    """Spell one typed use of a mixed-role source parameter or expression."""
    if role not in {"length", "angle", "count", "ratio"}:
        raise ModelError(f"unsupported Forge parameter role {role!r}")

    mixed_names = {
        parameter.name
        for parameter in model.parameters
        if len(parameter.roles) > 1
    }
    used_mixed = [
        parameter
        for parameter in parameters_in(value)
        if parameter.name in mixed_names
    ]
    if not used_mixed:
        return command_value(value)
    if len(used_mixed) != 1:
        raise ModelError(
            "mixed-role scalar expressions currently require one mixed source parameter"
        )

    if isinstance(value, Parameter):
        node = ScalarParameterRefIR(value.name)
    elif isinstance(value, Expression) and value.scalar_ir is not None:
        node = value.scalar_ir
    else:
        raise ModelError(
            "mixed-role Forge expression has no typed scalar semantics"
        )

    if not is_affine_scalar_expression(node):
        raise ModelError(
            "mixed-role Forge expression is outside affine scalar IR"
        )
    dependencies = scalar_parameter_names(node)
    return _native_expression(
        _role_scalar_expression_text(model, node, role),
        dependencies,
    )


def _negative_half(value):
    """Match the accepted SolidCraft symbolic half-expression spelling."""
    if isinstance(value, Parameter):
        return _native_expression(
            f"-{value.name} / 2",
            (value.name,),
        )
    if isinstance(value, Expression):
        expression = command_value(value)
        return _native_expression(
            f"-({expression}) / 2",
            expression.parameters,
        )
    return -pv(value) / 2


def _negative_value(value):
    if isinstance(value, Parameter):
        return _native_expression(f"-{value.name}", (value.name,))
    if isinstance(value, Expression):
        expression = command_value(value)
        return _native_expression(
            f"-({expression})",
            expression.parameters,
        )
    return -pv(value)


def _origin_box_corner(primitive: BoxIR, anchor):
    """Keep the already-qualified direct-Box expression spelling unchanged."""
    dimensions = (
        primitive.length,
        primitive.width,
        primitive.height,
    )
    corner = []
    for dimension, side in zip(dimensions, anchor):
        if side < 0:
            corner.append(0)
        elif side > 0:
            corner.append(_negative_value(dimension))
        else:
            corner.append(_negative_half(dimension))
    return corner


def _box_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str | None = None,
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, BoxIR):
        raise TypeError("SolidCraft box lowering requires PlacementIR(BoxIR)")

    _require_positive(primitive.length, "box length")
    _require_positive(primitive.width, "box width")
    _require_positive(primitive.height, "box height")
    selector = _DirectionSelector(node.anchor)

    params = {
        "length": command_value(primitive.length),
        "width": command_value(primitive.width),
        "height": command_value(primitive.height),
    }
    if operation is not None and node.anchor == (0, 0, 0):
        # Legacy CSG spelling keeps translated centered boxes as a native
        # centre placement rather than rewriting the equivalent solid by corner.
        params["center"] = [
            command_value(value) for value in node.point
        ]
    elif not node.explicit and node.anchor == (0, 0, 0):
        params["center"] = [0, 0, 0]
    elif not node.explicit and tuple(node.point) == (0, 0, 0):
        params["corner"] = [
            command_value(value)
            for value in _origin_box_corner(primitive, node.anchor)
        ]
    else:
        corner = _box_corner_from_anchor(
            primitive.length,
            primitive.width,
            primitive.height,
            node.point,
            selector,
        )
        params["corner"] = [
            command_value(value)
            for value in corner
        ]
    if operation is None:
        params["body_name"] = name
    else:
        params["operation"] = operation
        if operation == "new":
            params["body_name"] = name
        else:
            params["targets"] = [name]
    return _command("solid.box", **params)


def _cylinder_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, CylinderIR):
        raise TypeError(
            "SolidCraft cylinder lowering requires PlacementIR(CylinderIR)"
        )

    _require_positive(primitive.height, "cylinder height")
    _require_positive(primitive.diameter, "cylinder diameter")
    selector = _DirectionSelector(node.anchor)
    base = _cylinder_base_from_anchor(
        primitive.height,
        primitive.diameter,
        primitive.axis,
        node.point,
        selector,
    )
    params = {
        "height": command_value(primitive.height),
        "diameter": command_value(primitive.diameter),
        "base": [command_value(value) for value in base],
        "axis": primitive.axis,
        "operation": operation,
    }
    if operation == "new":
        params["body_name"] = name
    else:
        params["targets"] = [name]
    return _command("solid.cylinder", **params)


def _cone_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, ConeIR):
        raise TypeError(
            "SolidCraft cone lowering requires PlacementIR(ConeIR)"
        )

    _require_positive(primitive.height, "cone height")
    _require_positive(primitive.diameter, "cone diameter")
    if pv(primitive.top_diameter) < 0:
        raise ModelError("cone top diameter must be zero or positive")

    base = _cone_base_from_anchor(
        primitive.height,
        primitive.axis,
        node.point,
        _DirectionSelector(node.anchor),
    )
    params = {
        "height": command_value(primitive.height),
        "diameter": command_value(primitive.diameter),
        "top_diameter": command_value(primitive.top_diameter),
        "base": [command_value(value) for value in base],
        "axis": primitive.axis,
        "operation": operation,
    }
    if operation == "new":
        params["body_name"] = name
    else:
        params["targets"] = [name]
    return _command("solid.cone", **params)


def _sphere_command(
    node: PlacementIR,
    name: str,
    *,
    operation: str = "new",
) -> dict:
    primitive = node.primitive
    if not isinstance(primitive, SphereIR):
        raise TypeError(
            "SolidCraft sphere lowering requires PlacementIR(SphereIR)"
        )
    _require_positive(primitive.radius, "sphere radius")
    selector = _DirectionSelector(node.anchor)
    center = _sphere_center_from_anchor(
        primitive.radius,
        node.point,
        selector,
    )
    params = {
        "radius": command_value(primitive.radius),
        "center": [command_value(value) for value in center],
        "operation": operation,
    }
    if operation == "new":
        params["body_name"] = name
    else:
        params["targets"] = [name]
    return _command("solid.sphere", **params)


def _csg_primitive_command(
    node: PlacementIR,
    name: str,
    operation: str,
) -> dict:
    if isinstance(node.primitive, BoxIR):
        return _box_command(node, name, operation=operation)
    if isinstance(node.primitive, CylinderIR):
        return _cylinder_command(node, name, operation=operation)
    if isinstance(node.primitive, ConeIR):
        return _cone_command(node, name, operation=operation)
    if isinstance(node.primitive, SphereIR):
        return _sphere_command(node, name, operation=operation)
    raise ModelError(
        "portable SolidCraft primitive CSG does not support "
        f"{type(node.primitive).__name__}"
    )


def _parallel_box_edge_picks(
    node: PlacementIR,
    selection: ParallelEdgeSetIR,
) -> list[list[float]]:
    """Lower semantic principal Box edges to stable SolidCraft pick points."""
    if (
        not isinstance(node, PlacementIR)
        or not isinstance(node.primitive, BoxIR)
        or not isinstance(selection, ParallelEdgeSetIR)
        or selection.axis != "Z"
    ):
        raise ModelError(
            "portable SolidCraft parallel-edge selection currently requires "
            "Z-parallel edges of PlacementIR(BoxIR)"
        )

    primitive = node.primitive
    corner = _box_corner_from_anchor(
        primitive.length,
        primitive.width,
        primitive.height,
        node.point,
        _DirectionSelector(node.anchor),
    )
    x, y, z = (pv(value) for value in corner)
    length = pv(primitive.length)
    width = pv(primitive.width)
    height = pv(primitive.height)
    if not all(
        isfinite(value)
        for value in (x, y, z, length, width, height)
    ):
        raise ModelError("portable SolidCraft FilletIR Box geometry must be finite")

    mid_z = z + height / 2.0
    return [
        [x, y, mid_z],
        [x + length, y, mid_z],
        [x + length, y + width, mid_z],
        [x, y + width, mid_z],
    ]


def _fillet_commands(model: ModelIR, node: FilletIR, name: str) -> list[dict]:
    """Lower one constant-radius FilletIR through shared selector semantics."""
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft FilletIR requires typed BodyIR base")

    base_commands = _body_commands(model, node.base, name)
    topology, edges = _edge_selection_commands(
        node.base,
        node.edges,
        name,
        prior=base_commands,
    )

    radius = _require_positive(node.radius, "fillet radius")
    if isinstance(node.edges, ParallelEdgeSetIR):
        if node.edges.axis != "Z":
            raise ModelError(
                "portable SolidCraft parallel-edge selection currently requires Z"
            )
        width, depth, _corner, _center, _height = _typed_rectangular_base(
            node.base
        )
        if radius * 2 >= min(pv(width), pv(depth)):
            raise ModelError("fillet radius exceeds rectangular base dimensions")

    return [
        *base_commands,
        *topology,
        _command(
            "solid.fillet",
            edges=edges,
            radius=command_value(node.radius),
            body=name,
        ),
    ]


def _typed_rectangular_base(node: BodyIR):
    """Return stable rectangular-base semantics from typed body history."""
    if isinstance(node, PlacementIR) and isinstance(node.primitive, BoxIR):
        primitive = node.primitive
        selector = _DirectionSelector(node.anchor)
        corner = _box_corner_from_anchor(
            primitive.length,
            primitive.width,
            primitive.height,
            node.point,
            selector,
        )
        center = _primitive_center_from_anchor(
            (primitive.length, primitive.width, primitive.height),
            node.point,
            selector,
        )
        return (
            primitive.length,
            primitive.width,
            corner,
            center,
            primitive.height,
        )

    if isinstance(node, ExtrudeIR):
        if (
            node.sketch.plane.orientation != "XY"
            or node.sketch.plane.origin != (0, 0, 0)
            or node.direction != "positive"
            or len(node.sketch.profiles) != 1
            or not isinstance(node.sketch.profiles[0], RectangleProfileIR)
        ):
            raise ModelError(
                "anchored feature requires a positive XY rectangular body"
            )
        profile = node.sketch.profiles[0]
        corner = (
            _combine(profile.center[0], -half(profile.width)),
            _combine(profile.center[1], -half(profile.depth)),
            0,
        )
        center = (profile.center[0], profile.center[1], half(node.distance))
        return (
            profile.width,
            profile.depth,
            corner,
            center,
            node.distance,
        )

    if isinstance(node, FilletIR):
        return _typed_rectangular_base(node.base)
    if isinstance(node, ChamferIR):
        return _typed_rectangular_base(node.base)
    if isinstance(node, ShellIR):
        return _typed_rectangular_base(node.base)
    if isinstance(node, HoleIR):
        return _typed_rectangular_base(node.target)
    if isinstance(node, PlasticFeatureIR):
        return _typed_rectangular_base(node.target)
    if isinstance(node, (RectangularPatternIR, CircularPatternIR)):
        return _typed_rectangular_base(node.base)
    if isinstance(node, BooleanIR) and isinstance(node.target, BodyIR):
        return _typed_rectangular_base(node.target)

    raise ModelError(
        "anchored feature target has no qualified rectangular base semantics"
    )


def _typed_shell_thickness(node: BodyIR):
    if isinstance(node, ShellIR):
        return node.thickness
    if isinstance(node, FilletIR):
        return _typed_shell_thickness(node.base)
    if isinstance(node, ChamferIR):
        return _typed_shell_thickness(node.base)
    if isinstance(node, HoleIR):
        return _typed_shell_thickness(node.target)
    if isinstance(node, PlasticFeatureIR):
        return _typed_shell_thickness(node.target)
    if isinstance(node, (RectangularPatternIR, CircularPatternIR)):
        return _typed_shell_thickness(node.base)
    if isinstance(node, BooleanIR) and isinstance(node.target, BodyIR):
        return _typed_shell_thickness(node.target)
    return None


def _feature_offset_value(value, size, axis: str):
    if not isinstance(value, BoundOffsetIR):
        return value
    if value.axis != axis:
        raise ModelError(f"anchored {axis} offset uses {value.axis} bounds")
    if value.reference == "min":
        return _combine(-half(size), value.delta)
    if value.reference == "center":
        return value.delta
    if value.reference == "max":
        return _combine(half(size), value.delta)
    raise ModelError(f"unsupported anchored {axis} bound reference")


def _anchored_feature_position(target: BodyIR, placement: FeaturePlacementIR):
    if placement.mode != "anchored":
        raise ModelError("anchored feature lowering requires anchored placement")
    width, depth, corner, center, thickness = _typed_rectangular_base(target)
    offset_x = _feature_offset_value(placement.offset[0], width, "X")
    offset_y = _feature_offset_value(placement.offset[1], depth, "Y")
    x = _combine(center[0], offset_x)
    y = _combine(center[1], offset_y)

    if placement.parent_anchor == "top":
        z = _combine(corner[2], thickness)
    elif placement.parent_anchor == "bottom":
        z = corner[2]
    elif placement.parent_anchor == "inner_bottom":
        wall = _typed_shell_thickness(target)
        if wall is None:
            raise ModelError("Anchor.INNER_BOTTOM requires a typed ShellIR history")
        z = _combine(corner[2], wall)
    else:
        raise ModelError(
            "native placement/topology limitation: anchored feature currently "
            "requires TOP, BOTTOM or INNER_BOTTOM"
        )
    return x, y, z, thickness, corner


def _absolute_hole_command(
    model: ModelIR,
    node: HoleIR,
    name: str,
) -> dict:
    if node.placement.mode != "absolute" or node.placement.point is None:
        raise ModelError("absolute HoleIR requires absolute FeaturePlacementIR")

    params = {
        "position": (
            [command_value(value) for value in node.placement.point]
            if node.direction is not None
            else [pv(value) for value in node.placement.point]
        ),
        "targets": [name],
    }
    if node.diameter is not None:
        _require_positive(node.diameter, "hole diameter")
        params["diameter"] = command_value(node.diameter)
    if node.depth_mode == "distance":
        _require_positive(node.depth, "hole depth")
        params["depth"] = command_value(node.depth)
    elif node.depth_mode != "through_all":
        raise ModelError("portable SolidCraft HoleIR has unsupported depth mode")

    if node.direction is not None:
        params["direction"] = list(node.direction)

    if node.hole_type == "simple":
        pass
    elif node.hole_type == "counterbore":
        _require_positive(node.counterbore_diameter, "counterbore diameter")
        _require_positive(node.counterbore_depth, "counterbore depth")
        params.update(
            type="counterbore",
            cb_diameter=command_value(node.counterbore_diameter),
            cb_depth=command_value(node.counterbore_depth),
        )
    elif node.hole_type == "countersink":
        _require_positive(node.countersink_diameter, "countersink diameter")
        params.update(
            type="countersink",
            cs_diameter=command_value(node.countersink_diameter),
            cs_angle=_role_command_value(
                model,
                node.countersink_angle,
                "angle",
            ),
        )
    elif node.hole_type == "threaded":
        params["thread"] = node.thread
        if node.hand != "right":
            params["hand"] = node.hand
        if node.thread_depth is not None:
            _require_positive(node.thread_depth, "thread depth")
            params["thread_depth"] = command_value(node.thread_depth)
        if node.modeled:
            params["modeled"] = True
        if node.ease_out is not None:
            params["ease_out"] = (
                node.ease_out
                if isinstance(node.ease_out, str)
                else command_value(node.ease_out)
            )
    else:
        raise ModelError(
            f"portable SolidCraft HoleIR has unsupported type {node.hole_type!r}"
        )
    return _command("solid.hole", **params)


def _anchored_hole_commands(node: HoleIR, name: str) -> list[dict]:
    placement = node.placement
    if (
        placement.mode != "anchored"
        or placement.parent_anchor not in {"top", "bottom"}
        or placement.child_anchor != "bottom"
        or node.hole_type != "simple"
        or node.direction is not None
    ):
        raise ModelError(
            "portable anchored HoleIR currently lowers only simple "
            "TOP or BOTTOM placement with child Anchor.BOTTOM"
        )
    if node.diameter is None:
        raise ModelError("anchored HoleIR requires a diameter")
    _require_positive(node.diameter, "hole diameter")

    x, y, entry_z, thickness, corner = _anchored_feature_position(
        node.target,
        placement,
    )
    if node.depth_mode == "through_all":
        sketch_z = corner[2]
        distance = thickness
        direction = "positive"
    elif node.depth_mode == "distance":
        _require_positive(node.depth, "hole depth")
        sketch_z = entry_z
        distance = node.depth
        direction = (
            "negative"
            if placement.parent_anchor == "top"
            else "positive"
        )
    else:
        raise ModelError("portable anchored HoleIR has unsupported depth mode")

    plane = {"plane": "XY", "name": "Hole"}
    if pv(sketch_z):
        plane["offset"] = command_value(sketch_z)
    return [
        _command("sketch.create", **plane),
        _command(
            "sketch.circle.center",
            center=[command_value(x), command_value(y)],
            diameter=command_value(node.diameter),
        ),
        _command("sketch.finish"),
        _command(
            "solid.extrude",
            distance=command_value(distance),
            direction=direction,
            operation="cut",
            targets=[name],
            name="Hole",
        ),
    ]


def _hole_commands(model: ModelIR, node: HoleIR, name: str) -> list[dict]:
    """Lower Hole semantics after lowering the typed target history."""
    if not isinstance(node.target, BodyIR):
        raise ModelError("portable SolidCraft HoleIR requires typed BodyIR target")
    commands = _body_commands(model, node.target, name)
    if node.placement.mode == "absolute":
        return [
            *commands,
            _absolute_hole_command(model, node, name),
        ]
    if node.placement.mode == "anchored":
        return [*commands, *_anchored_hole_commands(node, name)]
    raise ModelError("portable SolidCraft HoleIR has unsupported placement mode")


def _plastic_feature_command_ir(
    node: PlasticFeatureIR,
    name: str,
) -> dict:
    placement = node.placement
    if placement.mode == "absolute":
        if placement.point is None:
            raise ModelError("absolute PlasticFeatureIR requires point")
        point = [pv(value) for value in placement.point]
    elif placement.mode == "anchored":
        if placement.child_anchor != "bottom":
            raise ModelError(
                "plastic features use their supporting point as Anchor.BOTTOM"
            )
        if placement.parent_anchor not in {"top", "bottom", "inner_bottom"}:
            raise ModelError(
                "plastic features require TOP, BOTTOM or INNER_BOTTOM placement"
            )
        x, y, z, _thickness, _corner = _anchored_feature_position(
            node.target,
            placement,
        )
        point = [pv(x), pv(y), pv(z)]
    else:
        raise ModelError("unsupported PlasticFeatureIR placement mode")

    feature = node.feature
    if isinstance(feature, LipFeatureIR):
        _require_positive(feature.width, "lip width")
        _require_positive(feature.height, "lip height")
        return _command(
            "plastic.lip",
            face=point,
            width=command_value(feature.width),
            height=command_value(feature.height),
            body=name,
        )

    if isinstance(feature, SnapFitFeatureIR):
        for value, label in (
            (feature.length, "snap-fit length"),
            (feature.thickness, "snap-fit thickness"),
            (feature.width, "snap-fit width"),
            (feature.catch_depth, "snap-fit catch depth"),
            (feature.catch_length, "snap-fit catch length"),
        ):
            _require_positive(value, label)
        params = {
            "position": point,
            "hook": list(feature.hook),
            "length": command_value(feature.length),
            "thickness": command_value(feature.thickness),
            "width": command_value(feature.width),
            "catch_depth": command_value(feature.catch_depth),
            "catch_length": command_value(feature.catch_length),
            "body": name,
        }
        if feature.direction is not None:
            params["direction"] = list(feature.direction)
        return _command("plastic.snap_fit", **params)

    if isinstance(feature, BossFeatureIR):
        _require_positive(feature.diameter, "boss diameter")
        _require_positive(feature.height, "boss height")
        params = {
            "position": point,
            "diameter": command_value(feature.diameter),
            "height": command_value(feature.height),
            "body": name,
        }
        if feature.hole_diameter is not None:
            _require_positive(feature.hole_diameter, "boss hole diameter")
            params["hole_diameter"] = command_value(feature.hole_diameter)
        if feature.direction is not None:
            params["direction"] = list(feature.direction)
        return _command("plastic.boss", **params)

    if isinstance(feature, RestFeatureIR):
        _require_positive(feature.width, "rest width")
        _require_positive(feature.height, "rest height")
        params = {
            "position": point,
            "width": command_value(feature.width),
            "height": command_value(feature.height),
            "body": name,
        }
        if feature.length is not None:
            _require_positive(feature.length, "rest length")
            params["length"] = command_value(feature.length)
        if feature.along is not None:
            params["along"] = list(feature.along)
        if feature.direction is not None:
            params["direction"] = list(feature.direction)
        return _command("plastic.rest", **params)

    raise ModelError(
        f"unsupported PlasticFeatureIR spec {type(feature).__name__}"
    )


def _plastic_feature_commands(
    model: ModelIR,
    node: PlasticFeatureIR,
    name: str,
) -> list[dict]:
    return [
        *_body_commands(model, node.target, name),
        _plastic_feature_command_ir(node, name),
    ]


def _boolean_commands(model: ModelIR, node: BooleanIR, name: str) -> list[dict]:
    """Lower generic BooleanIR while keeping backend tool support explicit."""
    if not isinstance(node.target, BodyIR) or not isinstance(node.tool, BodyIR):
        raise ModelError("portable SolidCraft BooleanIR requires typed body operands")

    commands = _body_commands(model, node.target, name)
    if isinstance(node.tool, PlacementIR):
        return [
            *commands,
            _csg_primitive_command(node.tool, name, node.operation),
        ]
    if isinstance(node.tool, ExtrudeIR):
        return _extrude_commands(
            model,
            node.tool,
            name,
            operation_override=node.operation,
            prior=commands,
        )
    if isinstance(node.tool, RevolveIR):
        return _revolve_commands(
            model,
            node.tool,
            name,
            operation_override=node.operation,
            prior=commands,
        )
    raise ModelError(
        "portable SolidCraft BooleanIR has no qualified lowering for tool "
        f"{type(node.tool).__name__}"
    )


_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}


def _principal_plane_offset(plane: PlaneIR, *, label: str):
    """Return one bounded principal-plane offset without baking symbols."""
    if not isinstance(plane, PlaneIR):
        raise ModelError(f"{label} requires PlaneIR")
    normal = _PLANE_NORMAL_INDEX[plane.orientation]
    for index, value in enumerate(plane.origin):
        if index == normal:
            continue
        if parameters_in(value) or abs(pv(value)) > 1e-12:
            raise ModelError(
                f"{label} currently requires zero in-plane PlaneIR origin"
            )
    return plane.origin[normal]


def _solidcraft_sketch_create(sketch) -> dict:
    """Create one standalone/world-frame Sketch from semantic frame intent."""
    normal = _PLANE_NORMAL_INDEX[sketch.plane.orientation]
    rotation = getattr(sketch, "rotation", None)
    in_plane = tuple(
        value
        for index, value in enumerate(sketch.plane.origin)
        if index != normal
    )
    explicit_frame = (
        rotation is not None
        or any(parameters_in(value) or abs(pv(value)) > 1e-12 for value in in_plane)
    )
    if explicit_frame:
        if any(parameters_in(value) for value in sketch.plane.origin):
            raise ModelError(
                "explicit rotated/in-plane Sketch frame currently requires fixed origin"
            )
        from ..sketches import _sketch_plane_frame
        return _command(
            "sketch.create",
            plane=_sketch_plane_frame(
                sketch.plane.orientation,
                origin=sketch.plane.origin,
                rotation=rotation,
            ),
            name=sketch.name,
        )

    offset = _principal_plane_offset(
        sketch.plane,
        label="portable SolidCraft Sketch IR",
    )
    params = {
        "name": sketch.name,
        "plane": sketch.plane.orientation,
    }
    if parameters_in(offset) or abs(pv(offset)) > 1e-12:
        params["offset"] = command_value(offset)
    return _command("sketch.create", **params)


def _typed_rectangular_support(node: BodyIR):
    """Find the typed axis-aligned Box datum underlying one body history."""
    if isinstance(node, PlacementIR) and isinstance(node.primitive, BoxIR):
        return node, None
    if isinstance(node, HoleIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, PlasticFeatureIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, ShellIR):
        placement, _wall = _typed_rectangular_support(node.base)
        return placement, node.thickness
    if isinstance(node, (ChamferIR, FilletIR)):
        return _typed_rectangular_support(node.base)
    if isinstance(node, (RectangularPatternIR, CircularPatternIR)):
        return _typed_rectangular_support(node.base)
    if isinstance(node, BooleanIR):
        return _typed_rectangular_support(node.target)
    if isinstance(node, ExtrudeIR) and node.target is not None:
        return _typed_rectangular_support(node.target)
    raise ModelError(
        "BOTTOM/CENTER/INNER_BOTTOM Sketch support currently requires "
        "a typed rectangular Box history"
    )


def _solidcraft_sketch_support_commands(
    sketch: SketchIR,
    name: str,
    *,
    prior: list[dict],
) -> tuple[list[dict], tuple]:
    """Lower semantic Sketch support and return backend-local XY origin."""
    support = sketch.support
    if support is None or support.parent is None:
        return [_solidcraft_sketch_create(sketch)], (0, 0)
    if not isinstance(support, SketchSupportIR):
        raise ModelError("portable SolidCraft Sketch support is malformed")

    if support.parent == "top":
        index = _next_face_query_index(prior)
        point_var = f"$face_point_{index}"
        index_var = f"$face_index_{index}"
        selector = {
            "field": "faces",
            "where": {"plane_normal": [0, 0, 1]},
            "max": "area",
        }
        face_query = _command("model.faces", body=name)
        face_query["bind"] = {
            point_var: {**selector, "select": "point"},
            index_var: {**selector, "select": "index"},
        }
        return [
            face_query,
            _command(
                "sketch.create",
                plane={
                    "face": point_var,
                    "body": name,
                    "index": index_var,
                },
                project_edges=False,
                name=sketch.name,
            ),
        ], (0, 0)

    placement, wall = _typed_rectangular_support(support.target)
    primitive = placement.primitive
    corner = _box_corner_from_anchor(
        primitive.length,
        primitive.width,
        primitive.height,
        placement.point,
        _DirectionSelector(placement.anchor),
    )
    center_x = _combine(corner[0], half(primitive.length))
    center_y = _combine(corner[1], half(primitive.width))
    if support.parent == "bottom":
        plane_z = corner[2]
    elif support.parent == "center":
        plane_z = _combine(corner[2], half(primitive.height))
    elif support.parent == "inner_bottom":
        if wall is None:
            raise ModelError(
                "INNER_BOTTOM Sketch support requires typed ShellIR history"
            )
        plane_z = _combine(corner[2], wall)
    else:
        raise ModelError(
            f"unsupported portable Sketch support anchor {support.parent!r}"
        )

    params = {"plane": "XY", "name": sketch.name}
    if parameters_in(plane_z) or abs(pv(plane_z)) > 1e-12:
        params["offset"] = command_value(plane_z)
    return [_command("sketch.create", **params)], (center_x, center_y)


def _next_sketch_index(commands: list[dict]) -> int:
    return 1 + sum(
        command.get("command") == "sketch.create"
        for command in commands
    )


def _solidcraft_relation_polygon_points(sketch) -> tuple[tuple, ...] | None:
    """Coalesce explicit semantic relations into SolidCraft's symbolic polyline.

    SolidCraft can retain authored point expressions directly in sketch.line,
    so duplicate solver relations are unnecessary. The relation graph remains
    the semantic source; this lowering only chooses an efficient native spelling.
    """
    relations = sketch.relations
    if relations is None:
        return None
    if not isinstance(relations, SketchRelationsIR):
        raise ModelError("portable SolidCraft Sketch relations require SketchRelationsIR")

    count = len(relations.points)
    expected_lines = tuple(
        (index, (index + 1) % count)
        for index in range(count)
    )
    actual_lines = tuple(
        (line.start, line.end)
        for line in relations.lines
    )
    if actual_lines != expected_lines:
        raise ModelError(
            "portable SolidCraft Sketch relations require one closed line loop"
        )

    if relations.coordinate_dimensions:
        if relations.constraints or relations.dimensions:
            raise ModelError(
                "portable SolidCraft coordinate relations must not mix relation families"
            )
        expected = {
            (point, axis): command_value(relations.points[point].position[index])
            for point in range(count)
            for index, axis in enumerate(("x", "y"))
        }
        actual = {
            (dimension.point, dimension.axis): command_value(dimension.value)
            for dimension in relations.coordinate_dimensions
        }
        if actual != expected or len(relations.coordinate_dimensions) != 2 * count:
            raise ModelError(
                "portable SolidCraft coordinate relations must drive every point coordinate"
            )
        return tuple(point.position for point in relations.points)

    if count != 4:
        raise ModelError(
            "portable SolidCraft #440 relations require one four-line rectangle"
        )

    expected_orientations = (
        "vertical",
        "horizontal",
        "vertical",
        "horizontal",
    )
    actual_orientations = [None] * count
    for constraint in relations.constraints:
        if actual_orientations[constraint.line] is not None:
            raise ModelError(
                "portable SolidCraft #440 relations require one orientation per line"
            )
        actual_orientations[constraint.line] = constraint.orientation
    if tuple(actual_orientations) != expected_orientations:
        raise ModelError(
            "portable SolidCraft #440 relations require V/H/V/H rectangle constraints"
        )
    if tuple(dimension.line for dimension in relations.dimensions) != (0, 1):
        raise ModelError(
            "portable SolidCraft #440 relations require the two driving edge dimensions"
        )

    return tuple(point.position for point in relations.points)


def _solidcraft_dimension_sum(left, right):
    """Match the stable standalone Sketch symbolic coordinate spelling."""
    if isinstance(left, (int, float)) and left == 0:
        return right
    if isinstance(right, (int, float)) and right == 0:
        return left
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left + right
    native_left = command_value(left)
    native_right = command_value(right)
    return _native_expression(
        f"({native_left}) + ({native_right})",
        tuple(sorted(_native_dependencies((native_left, native_right)))),
    )


def _solidcraft_profile_commands(
    sketch: SketchIR,
    profile: ProfileIR,
    *,
    profile_index: int,
    origin_offset=(0, 0),
) -> list[dict]:
    """Lower one semantic closed profile without reading frontend Shape.data."""

    def shifted(point):
        return (
            _solidcraft_dimension_sum(origin_offset[0], point[0]),
            _solidcraft_dimension_sum(origin_offset[1], point[1]),
        )
    if isinstance(profile, CircleProfileIR):
        _require_positive(profile.diameter, "circle diameter")
        return [
            _command(
                "sketch.circle.center",
                center=[
                    command_value(value)
                    for value in shifted(profile.center)
                ],
                diameter=command_value(profile.diameter),
            )
        ]

    if isinstance(
        profile,
        (RectangleProfileIR, RoundedRectangleProfileIR),
    ):
        _require_positive(profile.width, "sketch rectangle width")
        _require_positive(profile.depth, "sketch rectangle height")
        center = shifted(profile.center)
        x0 = _solidcraft_dimension_sum(center[0], -half(profile.width))
        y0 = _solidcraft_dimension_sum(center[1], -half(profile.depth))
        x1 = _solidcraft_dimension_sum(center[0], half(profile.width))
        y1 = _solidcraft_dimension_sum(center[1], half(profile.depth))
        params = {
            "p0": [command_value(x0), command_value(y0)],
            "p1": [command_value(x1), command_value(y1)],
        }
        if isinstance(profile, RoundedRectangleProfileIR):
            _require_positive(profile.radius, "sketch rounded rectangle radius")
            if pv(profile.radius) * 2 >= min(
                pv(profile.width),
                pv(profile.depth),
            ):
                raise ModelError(
                    "rounded rectangle radius exceeds half the shorter side"
                )
            params["radius"] = command_value(profile.radius)
            command = "sketch.rectangle.rounded"
        else:
            command = "sketch.rectangle.two_point"
        return [_command(command, **params)]

    if isinstance(profile, PolygonProfileIR):
        relation_points = _solidcraft_relation_polygon_points(sketch)
        points = (
            relation_points
            if relation_points is not None
            else profile.points
        )
        ids = (
            list(profile.segment_ids)
            if profile.segment_ids is not None
            else [
                chr(ord("a") + index)
                for index in range(len(points))
            ]
        )
        return [
            _command(
                "sketch.line",
                points=[
                    [
                        command_value(value)
                        for value in shifted(point)
                    ]
                    for point in points
                ],
                closed=True,
                ids=ids,
            )
        ]

    if not isinstance(profile, SlotProfileIR):
        raise ModelError(
            f"unsupported portable SolidCraft profile {type(profile).__name__}"
        )

    _require_positive(profile.width, "slot width")
    commands = []

    def intent(point):
        return tuple(
            _combine(
                origin_offset[index],
                _combine(profile.offset[index], value),
            )
            for index, value in enumerate(point)
        )

    def direct_point(point):
        values = [command_value(value) for value in intent(point)]
        if any(isinstance(value, str) for value in values):
            raise ModelError(
                "native Slot point coordinates currently require fixed values"
            )
        return values

    def seed_point(point):
        return [pv(value) for value in point]

    def same_intent(left, right):
        return command_value(left) == command_value(right)

    def parametric_straight(
        command_name,
        key_a,
        point_a,
        key_b,
        point_b,
        *,
        center_point=False,
    ):
        intent_a = intent(point_a)
        intent_b = intent(point_b)
        dx = pv(intent_b[0]) - pv(intent_a[0])
        dy = pv(intent_b[1]) - pv(intent_a[1])
        tolerance = 1e-9
        if abs(dy) <= tolerance and abs(dx) > tolerance:
            axis = 0
            mode = "horizontal"
            if not same_intent(intent_a[1], intent_b[1]):
                raise ModelError(
                    "parametric horizontal Slot endpoints must share "
                    "the same y-coordinate intent"
                )
        elif abs(dx) <= tolerance and abs(dy) > tolerance:
            axis = 1
            mode = "vertical"
            if not same_intent(intent_a[0], intent_b[0]):
                raise ModelError(
                    "parametric vertical Slot endpoints must share "
                    "the same x-coordinate intent"
                )
        else:
            raise ModelError(
                "parametric straight Slot endpoints currently require "
                "a horizontal or vertical axis"
            )

        delta = _dim_abs(_dim_sub(intent_b[axis], intent_a[axis]))
        if center_point:
            delta = delta * 2
        middle = (
            intent_a
            if center_point
            else (
                midpoint(intent_a[0], intent_b[0]),
                midpoint(intent_a[1], intent_b[1]),
            )
        )
        centre_line = f"$sketch_1_slot_{profile_index}_centre_line"
        middle_point = f"$sketch_1_slot_{profile_index}_middle"
        dimensioned = _command(
            "sketch.draw.dimensioned",
            command=command_name,
            params={
                key_a: seed_point(intent_a),
                key_b: seed_point(intent_b),
                "width": command_value(profile.width),
            },
            dimensions={"length": command_value(delta)},
        )
        dimensioned["bind"] = {
            centre_line: "centre_line",
            middle_point: "middle",
        }
        commands.append(dimensioned)
        commands.append(
            _command(
                "sketch.constraint.horizontal_vertical",
                line=centre_line,
                mode=mode,
            )
        )
        commands.append(
            _command(
                "sketch.dimension",
                entities=["origin", middle_point],
                type="horizontal",
                value=command_value(_dim_abs(middle[0])),
            )
        )
        commands.append(
            _command(
                "sketch.dimension",
                entities=["origin", middle_point],
                type="vertical",
                value=command_value(_dim_abs(middle[1])),
            )
        )

    points = profile.points
    if profile.construction == "center_to_center":
        a, b = points
        intents = (intent(a), intent(b))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.center_to_center",
                "p0",
                a,
                "p1",
                b,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.center_to_center",
                    p0=direct_point(a),
                    p1=direct_point(b),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "overall":
        a, b = points
        intents = (intent(a), intent(b))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.overall",
                "p0",
                a,
                "p1",
                b,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.overall",
                    p0=direct_point(a),
                    p1=direct_point(b),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "center_point":
        center, end = points
        intents = (intent(center), intent(end))
        if parameters_in(*(intents[0] + intents[1])):
            parametric_straight(
                "sketch.slot.center_point",
                "center",
                center,
                "end",
                end,
                center_point=True,
            )
        else:
            commands.append(
                _command(
                    "sketch.slot.center_point",
                    center=direct_point(center),
                    end=direct_point(end),
                    width=command_value(profile.width),
                )
            )
    elif profile.construction == "arc_three_point":
        start, through, end = points
        commands.append(
            _command(
                "sketch.slot.arc_three_point",
                start=direct_point(start),
                through=direct_point(through),
                end=direct_point(end),
                width=command_value(profile.width),
            )
        )
    elif profile.construction == "arc_center_end":
        center, start, end = points
        commands.append(
            _command(
                "sketch.slot.arc_center",
                center=direct_point(center),
                start=direct_point(start),
                end=direct_point(end),
                width=command_value(profile.width),
            )
        )
    elif profile.construction == "arc_center_sweep":
        center, start = points
        commands.append(
            _command(
                "sketch.slot.arc_center",
                center=direct_point(center),
                start=direct_point(start),
                width=command_value(profile.width),
                sweep=profile.sweep,
            )
        )
    else:
        raise ModelError(
            f"unsupported SlotProfileIR construction {profile.construction!r}"
        )
    return commands


def _extrude_commands(
    model: ModelIR,
    node: ExtrudeIR,
    name: str,
    *,
    operation_override: str | None = None,
    prior: list[dict] | None = None,
) -> list[dict]:
    """Lower typed Sketch/Extrude semantics, optionally as one CSG tool."""
    sketch = node.sketch
    if not isinstance(sketch, SketchIR):
        raise ModelError("portable SolidCraft ExtrudeIR requires SketchIR")

    if operation_override is not None and (
        operation_override not in {"join", "cut", "intersect"}
        or node.operation != "new_body"
        or node.target is not None
        or sketch.support is not None
    ):
        raise ModelError(
            "Boolean ExtrudeIR tool requires one standalone new-body ExtrudeIR"
        )

    commands = list(prior or [])
    if operation_override is None and node.operation != "new_body":
        if not isinstance(node.target, BodyIR):
            raise ModelError("attached ExtrudeIR requires typed body target")
        commands.extend(_body_commands(model, node.target, name))

    support_commands, local_origin = _solidcraft_sketch_support_commands(
        sketch,
        name,
        prior=commands,
    )
    sketch_index = _next_sketch_index(commands)
    commands.extend(support_commands)

    if sketch.graph is not None:
        commands.extend(
            _solidcraft_sketch_graph_commands(
                sketch.graph,
                sketch_index=sketch_index,
                model=model,
                origin_offset=local_origin,
            )
        )
    else:
        for index, profile in enumerate(sketch.profiles, start=1):
            commands.extend(
                _solidcraft_profile_commands(
                    sketch,
                    profile,
                    profile_index=index,
                    origin_offset=local_origin,
                )
            )
    commands.append(_command("sketch.finish"))

    params = {"direction": node.direction}
    effective_operation = operation_override or node.operation
    if effective_operation == "new_body":
        params["body_name"] = name
    else:
        params["operation"] = effective_operation
        params["targets"] = [name]
        params["name"] = sketch.name

    if node.through_all:
        params["through_all"] = True
    else:
        _require_positive(node.distance, "sketch extrusion distance")
        params["distance"] = _role_command_value(
            model,
            node.distance,
            "length",
        )

    if node.regions:
        # A single direct profile with no authored selector keeps the stable
        # implicit all-profile spelling.
        implicit_single = (
            len(node.regions) == 1
            and node.regions[0].selector is None
            and len(sketch.profiles) == 1
            and sketch.graph is not None
            and len(sketch.graph.entities) == 1
            and not sketch.graph.operations
        )
        if not implicit_single:
            picks = []
            exact = False
            for region in node.regions:
                try:
                    pick = _region_interior_point(sketch, region)
                except ValueError as exc:
                    raise ModelError(str(exc)) from exc
                picks.append({"point": [pick[0], pick[1]]})
                exact = exact or region.exact or region.selector is None
            params["profiles"] = picks
            if exact:
                params["exact_regions"] = True

    commands.append(_command("solid.extrude", **params))
    return commands


def _solidcraft_axis(axis: AxisLineIR):
    """Lower semantic axis intent without losing symbolic origin dependencies."""
    if (
        isinstance(axis.direction, str)
        and all(
            not parameters_in(value) and abs(pv(value)) <= 1e-12
            for value in axis.origin
        )
    ):
        return axis.direction

    direction = (
        {
            "X": [1.0, 0.0, 0.0],
            "Y": [0.0, 1.0, 0.0],
            "Z": [0.0, 0.0, 1.0],
        }[axis.direction]
        if isinstance(axis.direction, str)
        else list(axis.direction)
    )
    return {
        "origin": [command_value(value) for value in axis.origin],
        "dir": direction,
    }


def _revolve_commands(
    model: ModelIR,
    node: RevolveIR,
    name: str,
    *,
    operation_override: str | None = None,
    prior: list[dict] | None = None,
) -> list[dict]:
    """Lower semantic RevolveIR, optionally as one typed CSG tool."""
    sketch = node.sketch
    _principal_plane_offset(
        sketch.plane,
        label="portable SolidCraft RevolveIR",
    )
    if (
        len(sketch.profiles) != 1
        or not isinstance(sketch.profiles[0], PolygonProfileIR)
        or node.region != RegionIR(outer=0)
    ):
        raise ModelError("portable SolidCraft RevolveIR requires one polygon region")
    if not isinstance(node.axis, AxisLineIR) or node.direction is not None:
        raise ModelError(
            "portable SolidCraft RevolveIR requires one non-symmetric AxisLineIR"
        )

    try:
        _region_interior_point(sketch, node.region)
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    sweep = pv(node.angle)
    if not isfinite(sweep) or sweep <= 0 or sweep > 360:
        raise ModelError(
            "sketch revolve angle must be above 0 and at most 360 degrees"
        )

    profile = sketch.profiles[0]
    relation_points = _solidcraft_relation_polygon_points(sketch)
    authored_points = (
        relation_points
        if relation_points is not None
        else profile.points
    )
    ids = (
        list(profile.segment_ids)
        if profile.segment_ids is not None
        else [chr(ord("a") + index) for index in range(len(authored_points))]
    )
    if operation_override is not None and (
        operation_override not in {"join", "cut", "intersect"}
        or node.operation != "new_body"
        or node.target is not None
        or sketch.support is not None
    ):
        raise ModelError(
            "Boolean RevolveIR tool requires one standalone new-body RevolveIR"
        )

    revolve = {
        "sketch": sketch.name,
        "axis": _solidcraft_axis(node.axis),
        "angle": _role_command_value(model, node.angle, "angle"),
    }
    effective_operation = operation_override or node.operation
    base_commands = list(prior or [])
    if effective_operation == "new_body":
        if node.target is not None:
            raise ModelError("new-body RevolveIR must not have a target")
        revolve["body_name"] = name
    elif operation_override is not None:
        revolve["operation"] = effective_operation
        revolve["targets"] = [name]
    elif effective_operation == "cut":
        if (
            not isinstance(node.target, PlacementIR)
            or not isinstance(node.target.primitive, BoxIR)
        ):
            raise ModelError(
                "portable SolidCraft Revolve cut currently requires a Box target"
            )
        base_commands = [_box_command(node.target, name)]
        revolve["operation"] = "cut"
        revolve["targets"] = [name]
    else:
        raise ModelError(
            f"unsupported portable SolidCraft Revolve operation {effective_operation!r}"
        )

    return [
        *base_commands,
        _solidcraft_sketch_create(sketch),
        _command(
            "sketch.line",
            points=[
                [
                    _role_command_value(model, value, "length")
                    for value in point
                ]
                for point in authored_points
            ],
            closed=True,
            ids=ids,
        ),
        _command("sketch.finish"),
        _command("solid.revolve", **revolve),
    ]



def _next_face_query_index(commands: list[dict]) -> int:
    return 1 + sum(
        command.get("command") == "model.faces"
        for command in commands
    )


def _face_query_command(
    name: str,
    face: str,
    variable: str,
    *,
    select: str | None = None,
) -> dict:
    try:
        normal = _FACE_NORMALS[face]
    except KeyError as exc:
        raise ModelError(
            f"unsupported Forge face in IR: {face!r}"
        ) from exc
    selector = {
        "field": "faces",
        "where": {"plane_normal": normal},
        "max": "area",
    }
    if select is not None:
        selector["select"] = select
    command = _command("model.faces", body=name)
    command["bind"] = {variable: selector}
    return command


def _face_boundary_commands(
    selection: FaceBoundaryIR,
    name: str,
    *,
    prior: list[dict] | None = None,
) -> tuple[list[dict], str]:
    if not selection.faces:
        raise ModelError("portable SolidCraft face-boundary IR has no faces")

    commands = []
    previous_edges = None
    start = _next_face_query_index(prior or [])
    for offset, face in enumerate(selection.faces):
        index = start + offset
        face_variable = f"$topology_face_{index}"
        edge_variable = f"$topology_edges_{index}"
        commands.append(_face_query_command(name, face, face_variable))
        binding = {
            "field": "edges",
            "body": name,
            "boundary_of": face_variable,
        }
        if previous_edges is not None:
            binding["prepend"] = previous_edges
        commands.append(
            {
                "command": "model.edges",
                "params": {"body": name},
                "bind": {edge_variable: binding},
            }
        )
        previous_edges = edge_variable

    return commands, previous_edges


def _rectangular_edge_picks(
    base: BodyIR,
    vectors: tuple[tuple[int, int, int], ...],
) -> list[list[float]]:
    """Derive stable SolidCraft edge picks from typed rectangular-body semantics."""
    width, depth, corner, _center, height = _typed_rectangular_base(base)
    dimensions = (width, depth, height)
    picks = []
    for vector in vectors:
        point = []
        for minimum, dimension, side in zip(corner, dimensions, vector):
            if side < 0:
                value = minimum
            elif side > 0:
                value = _combine(minimum, dimension)
            else:
                value = _combine(minimum, half(dimension))
            point.append(pv(value))
        if not all(isfinite(value) for value in point):
            raise ModelError("rectangular edge selection must be finite")
        picks.append(point)
    return picks


def _profile_edge_picks(
    base: BodyIR,
    selection: ProfileEdgeSetIR,
) -> list[list[float]]:
    """Derive named Polygon-extrusion edge picks from semantic profile intent."""
    if (
        not isinstance(base, ExtrudeIR)
        or base.operation != "new_body"
        or base.through_all
        or base.distance is None
        or base.sketch.support is not None
        or base.sketch.plane.orientation != "XZ"
        or len(base.sketch.profiles) != 1
        or not isinstance(base.sketch.profiles[0], PolygonProfileIR)
    ):
        raise ModelError(
            "named profile edges require a standalone XZ polygon extrusion"
        )

    profile = base.sketch.profiles[0]
    names = profile.segment_ids
    if names is None:
        raise ModelError(
            "Polygon2D must define ids= or named points to select profile edges"
        )
    for pattern in selection.patterns:
        if not any(fnmatchcase(label, pattern) for label in names):
            raise ModelError(
                f"no polygon segment or vertex matches {pattern!r}"
            )

    matches = [
        index
        for index, label in enumerate(names)
        if any(
            fnmatchcase(label, pattern)
            for pattern in selection.patterns
        )
    ]
    plane_y = base.sketch.plane.origin[1]
    thickness = base.distance
    if base.direction == "symmetric":
        start_y = _combine(plane_y, -half(thickness))
        end_y = _combine(plane_y, half(thickness))
    elif base.direction == "positive":
        start_y = plane_y
        end_y = _combine(plane_y, thickness)
    elif base.direction == "negative":
        start_y = plane_y
        end_y = _combine(plane_y, -thickness)
    else:
        raise ModelError(
            "named profile edges require finite positive/negative/symmetric Extrude"
        )

    points = profile.points
    if selection.kind == "vertices":
        sweep_mid_y = midpoint(pv(start_y), pv(end_y))
        return [
            [pv(points[index][0]), sweep_mid_y, -pv(points[index][1])]
            for index in matches
        ]

    if selection.kind != "segments":
        raise ModelError(
            f"unsupported profile edge selection: {selection.kind}"
        )

    picks = []
    for y in (start_y, end_y):
        for index in matches:
            first = points[index]
            second = points[(index + 1) % len(points)]
            picks.append(
                [
                    midpoint(pv(first[0]), pv(second[0])),
                    pv(y),
                    -midpoint(pv(first[1]), pv(second[1])),
                ]
            )
    return picks


def _edge_selection_commands(
    base: BodyIR,
    selection,
    name: str,
    *,
    prior: list[dict] | None = None,
) -> tuple[list[dict], list[list[float]] | str]:
    """Lower shared semantic edge-selection intent to SolidCraft transport."""
    if isinstance(selection, FaceBoundaryIR):
        return _face_boundary_commands(
            selection,
            name,
            prior=prior,
        )

    if isinstance(selection, ParallelEdgeSetIR):
        if selection.axis != "Z":
            raise ModelError(
                "portable SolidCraft parallel-edge selection currently requires Z"
            )
        return [], _rectangular_edge_picks(
            base,
            (
                (-1, -1, 0),
                (1, -1, 0),
                (1, 1, 0),
                (-1, 1, 0),
            ),
        )

    if isinstance(selection, DirectionPairEdgeSetIR):
        return [], _rectangular_edge_picks(base, selection.vectors)

    if isinstance(selection, ProfileEdgeSetIR):
        return [], _profile_edge_picks(base, selection)

    if isinstance(selection, ExplicitEdgePicksIR):
        picks = [
            [pv(value) for value in point]
            for point in selection.points
        ]
        if not all(isfinite(value) for point in picks for value in point):
            raise ModelError("edge selection must be finite")
        return [], picks

    raise ModelError(
        f"unsupported portable SolidCraft edge selector {type(selection).__name__}"
    )


def _face_name_commands(
    prior: list[dict],
    selection: FaceSetIR,
    name: str,
) -> tuple[list[dict], list[str]]:
    if not isinstance(selection, FaceSetIR):
        raise ModelError("portable SolidCraft shell requires FaceSetIR")
    commands = []
    variables = []
    start = _next_face_query_index(prior)
    for offset, face in enumerate(selection.faces):
        variable = f"$topology_face_name_{start + offset}"
        commands.append(
            _face_query_command(
                name,
                face,
                variable,
                select="name",
            )
        )
        variables.append(variable)
    return commands, variables


def _chamfer_commands(model: ModelIR, node: ChamferIR, name: str) -> list[dict]:
    """Lower ChamferIR through the same shared semantic selector vocabulary."""
    _require_positive(node.distance, "chamfer distance")
    if node.distance2 is not None:
        _require_positive(node.distance2, "chamfer distance2")
    if node.flip and node.distance2 is None:
        raise ModelError("portable SolidCraft ChamferIR flip requires distance2")
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft ChamferIR requires typed BodyIR base")

    base_commands = _body_commands(model, node.base, name)
    topology, edges = _edge_selection_commands(
        node.base,
        node.edges,
        name,
        prior=base_commands,
    )
    params = {
        "body": name,
        "distance": command_value(node.distance),
        "edges": edges,
    }
    if node.distance2 is not None:
        params["distance2"] = command_value(node.distance2)
    if node.flip:
        params["flip"] = True

    return [
        *base_commands,
        *topology,
        _command("solid.chamfer", **params),
    ]


def _shell_commands(model: ModelIR, node: ShellIR, name: str) -> list[dict]:
    if not isinstance(node.base, BodyIR):
        raise ModelError("portable SolidCraft ShellIR requires typed BodyIR base")
    _require_positive(node.thickness, "shell thickness")
    base_commands = _body_commands(model, node.base, name)
    topology, faces = _face_name_commands(
        base_commands,
        node.open_faces,
        name,
    )
    return [
        *base_commands,
        *topology,
        _command(
            "solid.shell",
            faces=faces,
            thickness=command_value(node.thickness),
            body=name,
        ),
    ]


_AUTO_TYPED_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.extrude": "Extrude",
    "solid.hole": "Hole",
}


def _typed_feature_name(
    model: ModelIR,
    root: BodyIR,
    reference: FeatureRefIR,
    name: str,
) -> str:
    """Resolve semantic feature identity to private SolidCraft history naming."""
    feature = resolve_feature_ref(root, reference)
    if not isinstance(feature, BodyIR):
        raise ModelError(
            "portable SolidCraft pattern source must resolve to BodyIR history"
        )
    prefix = _body_commands(model, feature, name)
    if not prefix:
        raise ModelError("typed pattern source produced no SolidCraft history")
    last = prefix[-1]
    params = last.get("params", {})
    explicit = params.get("name")
    if isinstance(explicit, str) and explicit:
        return explicit
    command = last.get("command")
    base_name = _AUTO_TYPED_HISTORY_FEATURE_NAMES.get(command)
    if base_name is None:
        raise ModelError(
            "typed pattern source has no qualified stable SolidCraft feature identity"
        )
    ordinal = sum(row.get("command") == command for row in prefix)
    if ordinal < 1:
        raise ModelError("typed pattern source feature ordinal is missing")
    return f"{base_name}{ordinal}"


def _rectangular_pattern_commands(
    model: ModelIR,
    node: RectangularPatternIR,
    name: str,
) -> list[dict]:
    base = _body_commands(model, node.base, name)
    params = {
        "features": [
            _typed_feature_name(model, node.base, ref, name)
            for ref in node.sources
        ],
        "dir1": list(node.direction1),
        "count1": _role_command_value(model, node.count1, "count"),
        "spacing1": _role_command_value(model, node.spacing1, "length"),
        "alignment": node.alignment1,
        "reversed": node.reversed1,
    }
    if node.direction2 is not None:
        params.update(
            dir2=list(node.direction2),
            count2=_role_command_value(model, node.count2, "count"),
            spacing2=_role_command_value(model, node.spacing2, "length"),
            alignment2=node.alignment2,
            reversed2=node.reversed2,
        )
    return [
        *base,
        _command("solid.pattern.rectangular", **params),
    ]


def _circular_pattern_commands(
    model: ModelIR,
    node: CircularPatternIR,
    name: str,
) -> list[dict]:
    base = _body_commands(model, node.base, name)
    params = {
        "features": [
            _typed_feature_name(model, node.base, ref, name)
            for ref in node.sources
        ],
        "axis": _solidcraft_axis(node.axis),
        "count": _role_command_value(model, node.count, "count"),
        "alignment": node.alignment,
        "reversed": node.reversed,
    }
    if node.angle is not None:
        params["angle"] = (
            _role_command_value(model, node.angle, "angle")
            if isinstance(node.angle, Parameter)
            else f"{number_text(node.angle)} deg"
        )
    return [
        *base,
        _command("solid.pattern.circular", **params),
    ]


def _sheet_rule_command(model: ModelIR, rule: SheetRuleIR) -> dict:
    if not isinstance(rule, SheetRuleIR):
        raise ModelError("typed sheet body requires SheetRuleIR")
    _require_positive(rule.thickness, "sheet metal thickness")
    _require_positive(rule.bend_radius, "sheet metal bend radius")
    k = pv(rule.k_factor)
    if not isfinite(k) or not 0 < k < 1:
        raise ModelError("sheet metal k_factor must be between 0 and 1")
    return _command(
        "sheet.manage_rules",
        name=rule.name,
        thickness=_role_command_value(model, rule.thickness, "length"),
        k_factor=_role_command_value(model, rule.k_factor, "ratio"),
        bend_radius=_role_command_value(model, rule.bend_radius, "length"),
        active=True,
    )


def _sketch_chain_geometry_commands(
    chain: SketchChainIR,
    *,
    model: ModelIR | None = None,
    bind_curves: bool = False,
    binding_prefix: str = "$contour_curves",
    origin_offset=(0, 0),
) -> tuple[list[dict], str | None]:
    """Lower shared semantic line/arc chain geometry without Sketch support."""
    if not isinstance(chain, SketchChainIR):
        raise ModelError("Sketch chain geometry requires SketchChainIR")
    commands = []
    curve_variable = None
    curve_count = 0
    previous_line_id = None
    line_count = 0

    def value(item):
        return (
            _role_command_value(model, item, "length")
            if model is not None
            else command_value(item)
        )

    def point(coordinates):
        shifted = (
            _solidcraft_dimension_sum(origin_offset[0], coordinates[0]),
            _solidcraft_dimension_sum(origin_offset[1], coordinates[1]),
        )
        return [value(shifted[0]), value(shifted[1])]

    def append_curve(command):
        nonlocal curve_variable, curve_count
        if bind_curves:
            curve_count += 1
            next_variable = f"{binding_prefix}_{curve_count}"
            binding = (
                "curves"
                if curve_variable is None
                else {"field": "curves", "prepend": curve_variable}
            )
            command["bind"] = {next_variable: binding}
            curve_variable = next_variable
        commands.append(command)

    for segment in chain.segments:
        if segment.kind == "line":
            line_count += 1
            line_id = f"l{line_count}"
            params = {
                "points": [point(segment.start), point(segment.end)],
                "connect": True,
            }
            if not chain.closed:
                params["ids"] = [line_id]
            append_curve(_command("sketch.line", **params))
            previous_line_id = line_id
            continue

        if segment.kind == "arc_tangent":
            if previous_line_id is None:
                raise ModelError(
                    "semantic tangent Sketch arc requires preceding line"
                )
            append_curve(
                _command(
                    "sketch.arc.tangent",
                    start=f"{previous_line_id}.end",
                    curve=previous_line_id,
                    end=point(segment.end),
                )
            )
            previous_line_id = None
            continue

        if segment.kind == "arc_three_point":
            append_curve(
                _command(
                    "sketch.arc.three_point",
                    start=point(segment.start),
                    end=point(segment.end),
                    through=point(segment.through),
                    connect=True,
                )
            )
            previous_line_id = None
            continue

        if segment.kind == "arc_center_point":
            append_curve(
                _command(
                    "sketch.arc.center_point",
                    center=point(segment.center),
                    start=point(segment.start),
                    end=point(segment.end),
                    clockwise=segment.clockwise,
                    connect=True,
                )
            )
            previous_line_id = None
            continue

        raise ModelError(
            f"unsupported semantic Sketch chain segment {segment.kind!r}"
        )

    if bind_curves and curve_variable is None:
        raise ModelError("semantic Sketch chain has no curves to consume")
    return commands, curve_variable


def _sheet_chain_commands(
    model: ModelIR,
    chain: SketchChainIR,
    *,
    bind_curves: bool = False,
) -> tuple[list[dict], str | None]:
    """Lower semantic connected Sketch intent with its standalone support."""
    if not isinstance(chain, SketchChainIR):
        raise ModelError("sheet Sketch path requires SketchChainIR")
    if chain.plane is None:
        raise ModelError("sheet Sketch path requires semantic PlaneIR support")
    geometry, curve_variable = _sketch_chain_geometry_commands(
        chain,
        model=model,
        bind_curves=bind_curves,
    )
    return [
        _solidcraft_sketch_create(chain),
        *geometry,
        _command("sketch.finish"),
    ], curve_variable


def _solidcraft_sketch_graph_commands(
    graph: SketchEntityGraphIR,
    *,
    sketch_index: int = 1,
    model: ModelIR | None = None,
    origin_offset=(0, 0),
) -> list[dict]:
    """Lower support-independent Sketch graph contents.

    Support creation and consuming solid features are deliberately owned by
    #561. Native/replay identities are created only in this backend.
    """
    if not isinstance(graph, SketchEntityGraphIR):
        raise TypeError("Sketch graph lowering requires SketchEntityGraphIR")
    if type(sketch_index) is not int or sketch_index < 1:
        raise ModelError("Sketch graph index must be positive")

    commands = []
    referenced_entities = {
        operation.source.index
        for operation in graph.operations
        if operation.source.kind == "entity"
    }

    def entity_variable(index):
        return f"$sketch_{sketch_index}_profile_{index + 1}"

    def operation_variable(index):
        return f"$sketch_{sketch_index}_operation_{index + 1}"

    def source_variable(reference: SketchEntityRefIR):
        if reference.kind == "entity":
            entity = graph.entities[reference.index]
            if isinstance(entity, SketchChainIR):
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            return entity_variable(reference.index)
        return operation_variable(reference.index)

    for index, entity in enumerate(graph.entities):
        variable = entity_variable(index)
        if isinstance(entity, TextEntityIR):
            _require_positive(entity.height, "sketch text height")
            rows = [
                _command(
                    "sketch.text",
                    text=entity.text,
                    at=[
                        command_value(
                            _solidcraft_dimension_sum(
                                origin_offset[index],
                                value,
                            )
                        )
                        for index, value in enumerate(entity.position)
                    ],
                    height=command_value(entity.height),
                    font=entity.font,
                )
            ]
        elif isinstance(entity, SketchChainIR):
            rows, _binding = _sketch_chain_geometry_commands(
                entity,
                model=model,
                origin_offset=origin_offset,
            )
        else:
            dummy = SketchIR(
                name="Graph",
                plane=PlaneIR("XY"),
                profiles=(entity,),
            )
            rows = _solidcraft_profile_commands(
                dummy,
                entity,
                profile_index=index + 1,
                origin_offset=origin_offset,
            )

        if index in referenced_entities:
            if isinstance(entity, SketchChainIR):
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            if not rows:
                raise ModelError(
                    "semantic Sketch entity produced no SolidCraft curves"
                )
            rows[0].setdefault("bind", {})[variable] = "curves"
        commands.extend(rows)

    for chain in graph.open_chains:
        rows, _binding = _sketch_chain_geometry_commands(
            chain,
            model=model,
            origin_offset=origin_offset,
        )
        commands.extend(rows)

    for index, operation in enumerate(graph.operations):
        source = source_variable(operation.source)
        variable = operation_variable(index)
        if isinstance(operation, SketchRectangularPatternIR):
            params = {
                "entities": source,
                "count": command_value(operation.count),
                "spacing": command_value(operation.spacing),
                "dir": list(operation.direction),
            }
            has_second_direction = (
                pv(operation.count2) != 1
                or bool(parameters_in(operation.count2))
            )
            if has_second_direction:
                params["count2"] = command_value(operation.count2)
                if operation.spacing2 is not None:
                    params["spacing2"] = command_value(operation.spacing2)
                if operation.direction2 is not None:
                    params["dir2"] = list(operation.direction2)
            if operation.alignment != "right":
                params["alignment"] = operation.alignment
            if has_second_direction and operation.alignment2 != "right":
                params["alignment2"] = operation.alignment2
            if operation.reversed:
                params["reversed"] = True
            if has_second_direction and operation.reversed2:
                params["reversed2"] = True
            row = _command("sketch.pattern.rectangular", **params)
            row["bind"] = {
                variable: {
                    "field": "curves",
                    "prepend": source,
                }
            }
        elif isinstance(operation, SketchMirrorIR):
            row = _command(
                "sketch.mirror",
                entities=source,
                line=operation.axis,
            )
            row["bind"] = {variable: "curves"}
        else:
            raise ModelError(
                f"unsupported Sketch operation IR {type(operation).__name__}"
            )
        commands.append(row)

    return commands


def _sheet_base_commands(
    model: ModelIR,
    node: SheetBaseIR,
    name: str,
) -> list[dict]:
    rule = _sheet_rule_command(model, node.rule)
    blank = node.blank
    if isinstance(blank, SketchChainIR):
        if not blank.closed:
            raise ModelError("sheet base chain must be closed")
        sketch, _curves = _sheet_chain_commands(model, blank)
        sketch_name = blank.name
    else:
        if len(blank.profiles) != 1:
            raise ModelError("typed sheet base requires one closed profile")
        sketch = [_solidcraft_sketch_create(blank)]
        sketch.extend(
            _solidcraft_profile_commands(
                blank,
                blank.profiles[0],
                profile_index=1,
            )
        )
        sketch.append(_command("sketch.finish"))
        sketch_name = blank.name
    return [
        rule,
        *sketch,
        _command(
            "sheet.flange",
            type="base",
            sketch=sketch_name,
            rule=node.rule.name,
            body_name=name,
        ),
    ]


def _sheet_contour_commands(
    model: ModelIR,
    node: SheetContourFlangeIR,
    name: str,
) -> list[dict]:
    rule = _sheet_rule_command(model, node.rule)
    sketch, curves = _sheet_chain_commands(
        model,
        node.contour,
        bind_curves=True,
    )
    params = {
        "type": "contour",
        "sketch": node.contour.name,
        "curves": curves,
        "distance": _role_command_value(model, node.distance, "length"),
        "rule": node.rule.name,
        "body_name": name,
    }
    if node.flip:
        params["flip"] = True
    if node.reverse:
        params["reverse"] = True
    return [rule, *sketch, _command("sheet.flange", **params)]


def _sheet_fold_commands(
    model: ModelIR,
    node: SheetFoldIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "angle": _role_command_value(model, node.angle, "angle"),
        "position": node.position,
        "flip": node.flip,
        "body": name,
    }
    if isinstance(node.line, SketchChainIR):
        sketch, _curves = _sheet_chain_commands(model, node.line)
        commands.extend(sketch)
        params["sketch"] = node.line.name
        params["curve"] = "l1"
    else:
        params["points"] = [
            [command_value(value) for value in point]
            for point in node.line
        ]
    if node.fixed is not None:
        params["fixed"] = [command_value(value) for value in node.fixed]
    return [*commands, _command("sheet.fold", **params)]


def _sheet_edge_flange_commands(
    model: ModelIR,
    node: SheetEdgeFlangeIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "type": "edge",
        "edges": [
            [command_value(value) for value in point]
            for point in node.edges
        ],
        "height": _role_command_value(model, node.height, "length"),
        "angle": _role_command_value(model, node.angle, "angle"),
        "body": name,
    }
    if node.height_from is not None:
        params["height_from"] = node.height_from
    if node.position is not None:
        params["position"] = node.position
    if node.flip:
        params["flip"] = True
    return [*commands, _command("sheet.flange", **params)]


def _sheet_hem_commands(
    model: ModelIR,
    node: SheetHemIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "edges": [
            [command_value(value) for value in point]
            for point in node.edges
        ],
        "length": _role_command_value(model, node.length, "length"),
        "body": name,
    }
    if node.gap is not None:
        params["gap"] = _role_command_value(model, node.gap, "length")
    if node.flip:
        params["flip"] = True
    return [*commands, _command("sheet.hem", **params)]


def _sheet_path_flange_commands(
    model: ModelIR,
    node: SheetPathFlangeIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    sketch, curves = _sheet_chain_commands(
        model,
        node.path,
        bind_curves=True,
    )
    params = {
        "edge": [command_value(value) for value in node.edge],
        "sketch": node.path.name,
        "curves": curves,
        "body": name,
    }
    if node.radius is not None:
        params["radius"] = _role_command_value(
            model,
            node.radius,
            "length",
        )
    return [
        *commands,
        *sketch,
        _command("sheet.path_flange", **params),
    ]


def _sheet_perforate_commands(
    model: ModelIR,
    node: SheetPerforateIR,
    name: str,
) -> list[dict]:
    commands = _body_commands(model, node.base, name)
    params = {
        "diameter": _role_command_value(model, node.diameter, "length"),
        "pitch": _role_command_value(model, node.pitch, "length"),
        "body": name,
    }
    if node.margin is not None:
        params["margin"] = _role_command_value(model, node.margin, "length")
    if node.pattern != "staggered":
        params["pattern"] = node.pattern
    return [*commands, _command("sheet.perforate", **params)]


def _body_commands(model: ModelIR, node: BodyIR, name: str) -> list[dict]:
    """Lower one typed semantic body history without re-reading Shape.data."""
    if isinstance(node, SheetBaseIR):
        return _sheet_base_commands(model, node, name)

    if isinstance(node, SheetContourFlangeIR):
        return _sheet_contour_commands(model, node, name)

    if isinstance(node, SheetFoldIR):
        return _sheet_fold_commands(model, node, name)

    if isinstance(node, SheetEdgeFlangeIR):
        return _sheet_edge_flange_commands(model, node, name)

    if isinstance(node, SheetHemIR):
        return _sheet_hem_commands(model, node, name)

    if isinstance(node, SheetPathFlangeIR):
        return _sheet_path_flange_commands(model, node, name)

    if isinstance(node, SheetPerforateIR):
        return _sheet_perforate_commands(model, node, name)

    if isinstance(node, PlacementIR):
        if isinstance(node.primitive, BoxIR):
            return [_box_command(node, name)]
        if isinstance(node.primitive, CylinderIR):
            return [_cylinder_command(node, name)]
        if isinstance(node.primitive, ConeIR):
            return [_cone_command(node, name)]
        if isinstance(node.primitive, SphereIR):
            return [_sphere_command(node, name)]
        raise TypeError(
            f"unsupported SolidCraft placed primitive "
            f"{type(node.primitive).__name__}"
        )

    if isinstance(node, ExtrudeIR):
        return _extrude_commands(model, node, name)

    if isinstance(node, BooleanIR):
        return _boolean_commands(model, node, name)

    if isinstance(node, HoleIR):
        return _hole_commands(model, node, name)

    if isinstance(node, PlasticFeatureIR):
        return _plastic_feature_commands(model, node, name)

    if isinstance(node, FilletIR):
        return _fillet_commands(model, node, name)

    if isinstance(node, RevolveIR):
        return _revolve_commands(model, node, name)

    if isinstance(node, ChamferIR):
        return _chamfer_commands(model, node, name)

    if isinstance(node, ShellIR):
        return _shell_commands(model, node, name)

    if isinstance(node, RectangularPatternIR):
        return _rectangular_pattern_commands(model, node, name)

    if isinstance(node, CircularPatternIR):
        return _circular_pattern_commands(model, node, name)

    raise TypeError(f"not a portable Forge BodyIR node: {type(node).__name__}")


def _portable_commands(model: ModelIR, name: str) -> list[dict]:
    node = model.root
    if not isinstance(node, BodyIR):
        raise TypeError(f"not a portable Forge IR node: {type(node).__name__}")
    return [
        *_parameter_commands(model),
        *_body_commands(model, node, name),
    ]


def _boolean_command_count(node) -> int:
    """Return SolidCraft geometry command count for one typed Boolean subtree."""
    if isinstance(node, PlacementIR):
        return 1
    if isinstance(node, FilletIR):
        return 2
    if isinstance(node, BooleanIR):
        return _boolean_command_count(node.target) + 1
    raise ModelError(
        "portable SolidCraft Boolean feature references require typed CSG nodes"
    )


def _boolean_feature_command_index(
    root: BooleanIR,
    reference: FeatureRefIR,
) -> int:
    """Map semantic target/tool history roles to backend-local command order."""
    resolve_feature_ref(root, reference)
    segments = reference.path[1:]
    node = root
    offset = 0

    if not segments:
        # A BooleanIR feature is represented natively by the command applying
        # its tool to its target.
        return _boolean_command_count(node.target)

    for position, segment in enumerate(segments):
        last = position == len(segments) - 1
        if not isinstance(node, BooleanIR):
            raise ModelError(
                "SolidCraft feature reference descends beyond Boolean history"
            )
        if segment == "tool":
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a CSG tool"
                )
            return offset + _boolean_command_count(node.target)
        if segment != "target":
            raise ModelError(
                f"unsupported SolidCraft semantic feature role {segment!r}"
            )

        target = node.target
        if isinstance(target, PlacementIR):
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a primitive target"
                )
            return offset
        if isinstance(target, FilletIR):
            if not last:
                raise ModelError(
                    "SolidCraft feature reference cannot descend through a Fillet target"
                )
            return offset + 1
        if not isinstance(target, BooleanIR):
            raise ModelError(
                "SolidCraft feature reference target is not typed Boolean history"
            )
        if last:
            return offset + _boolean_command_count(target.target)
        node = target

    raise ModelError("SolidCraft feature reference did not resolve to a command")


def _configured_feature_command_index(
    model: ModelIR,
    configuration: ConfigurationIR,
    commands: list[dict],
) -> int:
    """Resolve semantic feature identity to one backend-local native command."""
    if (
        len(configuration.columns) != 1
        or not isinstance(configuration.columns[0], SuppressionColumnIR)
    ):
        raise ModelError(
            "portable SolidCraft configuration requires one suppression feature"
        )
    reference = configuration.columns[0].feature

    if isinstance(model.root, RevolveIR) and reference == FeatureRefIR(("root",)):
        indexes = [
            index
            for index, command in enumerate(commands)
            if command.get("command") == "solid.revolve"
        ]
        if len(indexes) != 1:
            raise ModelError(
                "portable SolidCraft configuration root must resolve to one Revolve feature"
            )
        return indexes[0]

    if isinstance(model.root, BooleanIR):
        geometry_index = _boolean_feature_command_index(model.root, reference)
        return len(model.parameters) + geometry_index

    raise ModelError(
        "portable SolidCraft configuration feature is outside qualified history"
    )


def _portable_configuration_commands(
    model: ModelIR,
    configuration: ConfigurationIR,
    commands: list[dict],
) -> list[dict]:
    """Lower semantic suppression rows without source-object/native-id lookup."""
    from ..configurations import _row_variable

    commands = [dict(command) for command in commands]
    index = _configured_feature_command_index(model, configuration, commands)

    feature_name = "$config_name_1"
    target = dict(commands[index])
    bindings = dict(target.get("bind", {}))
    bindings[feature_name] = "name"
    target["bind"] = bindings
    commands[index] = target

    commands.append(
        _command(
            "config.configure",
            features=[feature_name],
        )
    )

    def row_binding(variable, row_name):
        return {
            variable: {
                "field": "rows",
                "where": {"name": row_name},
                "select": "id",
            }
        }

    row_refs = {}
    first = configuration.rows[0].name
    if first != "Default":
        rename = _command(
            "config.row",
            name="Default",
            rename=first,
        )
        variable = _row_variable(first)
        rename["bind"] = row_binding(variable, first)
        row_refs[first] = variable
        commands.append(rename)

    for row in configuration.rows:
        update = _command(
            "config.row",
            name=row.name,
            values={
                f"suppress:{feature_name}": (
                    "true" if row.cells[0] else "false"
                ),
            },
        )
        if row.name not in row_refs:
            variable = _row_variable(row.name)
            update["bind"] = row_binding(variable, row.name)
            row_refs[row.name] = variable
        commands.append(update)

    commands.append(
        _command(
            "config.activate",
            row=row_refs[configuration.active],
        )
    )
    commands.append(_command("config.table"))
    return commands


def compile_ir_commands_with_dependencies(model: ModelIR, name: str):
    """Lower one ModelIR to a flat native command sequence.

    This is the shared SolidCraft boundary used both for a standalone design
    and for one reusable component definition inside AssemblyIR. Replay
    wrapping belongs to the enclosing design, so native occurrence/component
    transport never needs to enter semantic ModelIR.
    """
    if not isinstance(model, ModelIR):
        raise TypeError("SolidCraft backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if isinstance(model.root, LegacyShapeIR):
        from ..compiler import _compile_model_commands
        commands = _compile_model_commands(model.root.shape, name)
        return commands, _native_dependencies(commands)

    commands = _portable_commands(model, name)
    if model.configuration is not None:
        commands = _portable_configuration_commands(
            model,
            model.configuration,
            commands,
        )
    return commands, _native_dependencies(commands)


def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Lower one normalized Forge model to SolidCraft native intent."""
    commands, dependencies = compile_ir_commands_with_dependencies(
        model,
        name,
    )
    plain = _plain_command_value(commands)
    document = (
        replay_document(plain)
        if any("bind" in command for command in plain)
        else {"commands": plain}
    )
    return document, dependencies


def compile_ir(model: ModelIR, name: str) -> dict:
    return compile_ir_with_dependencies(model, name)[0]


__all__ = [
    "compile_ir",
    "compile_ir_with_dependencies",
    "compile_ir_commands_with_dependencies",
]
