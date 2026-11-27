"""Lower typed Forge semantic IR to native SolidCraft commands.

Portable IR nodes are lowered directly here. LegacyShapeIR is the explicit
transition boundary for stable Forge functionality that has not yet migrated
to typed semantic IR.
"""
from __future__ import annotations

from math import isfinite

from ..compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from ..core import (
    Expression,
    Parameter,
    _DirectionSelector,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _cylinder_base_from_anchor,
    _sphere_center_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    command_value,
    number_text,
    parameters_in,
)
from ..ir import (
    AxisLineIR,
    BodyIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CircularPatternIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FeatureRefIR,
    FilletIR,
    HoleIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PolygonProfileIR,
    RegionIR,
    RectangularPatternIR,
    RevolveIR,
    SketchRelationsIR,
    ShellIR,
    SphereIR,
    SuppressionColumnIR,
    _region_interior_point,
    resolve_feature_ref,
)
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
    if role not in {"length", "angle", "count"}:
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


def _fillet_commands(node: FilletIR, name: str) -> list[dict]:
    """Lower one bounded constant-radius FilletIR."""
    if (
        not isinstance(node.base, PlacementIR)
        or not isinstance(node.base.primitive, BoxIR)
    ):
        raise ModelError(
            "portable SolidCraft FilletIR currently requires a Box base"
        )

    if isinstance(node.edges, ParallelEdgeSetIR):
        if node.edges.axis != "Z":
            raise ModelError(
                "portable SolidCraft FilletIR parallel edges must be Z"
            )
        topology = []
        edges = _parallel_box_edge_picks(node.base, node.edges)
    elif isinstance(node.edges, FaceBoundaryIR):
        if node.edges.faces != ("top",):
            raise ModelError(
                "portable SolidCraft FilletIR face boundary must be TOP"
            )
        topology, edges = _face_boundary_commands(node.edges, name)
    else:
        raise ModelError(
            "portable SolidCraft FilletIR has unsupported edge semantics"
        )

    radius = _require_positive(node.radius, "fillet radius")
    primitive = node.base.primitive
    if radius * 2 >= min(pv(primitive.length), pv(primitive.width)):
        raise ModelError("fillet radius exceeds rectangular base dimensions")

    return [
        _box_command(node.base, name),
        *topology,
        _command(
            "solid.fillet",
            edges=edges,
            radius=command_value(node.radius),
            body=name,
        ),
    ]


def _hole_commands(model: ModelIR, node: HoleIR, name: str) -> list[dict]:
    """Lower one semantic explicit Hole-family history chain."""
    if not isinstance(node.target, BodyIR):
        raise ModelError("portable SolidCraft HoleIR requires typed BodyIR target")
    commands = _body_commands(model, node.target, name)

    params = {
        "position": (
            [command_value(value) for value in node.point]
            if node.direction is not None
            else [pv(value) for value in node.point]
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
            cs_angle=node.countersink_angle,
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

    return [*commands, _command("solid.hole", **params)]


def _boolean_commands(node: BooleanIR, name: str) -> list[dict]:
    """Flatten one bounded left-associated semantic CSG tree in source order."""
    commands = []
    if isinstance(node.target, BooleanIR):
        commands.extend(_boolean_commands(node.target, name))
    elif isinstance(node.target, FilletIR):
        commands.extend(_fillet_commands(node.target, name))
    elif isinstance(node.target, PlacementIR):
        commands.append(_csg_primitive_command(node.target, name, "new"))
    else:
        raise ModelError("portable SolidCraft BooleanIR has unsupported target")

    commands.append(
        _csg_primitive_command(node.tool, name, node.operation)
    )
    return commands


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


def _extrude_commands(node: ExtrudeIR, name: str) -> list[dict]:
    """Lower qualified Sketch/Profile + Extrude IR without backend parsing."""
    sketch = node.sketch
    _principal_plane_offset(
        sketch.plane,
        label="portable SolidCraft Sketch IR",
    )
    if len(node.regions) != 1:
        raise ModelError("portable SolidCraft Extrude IR requires one region")

    region = node.regions[0]
    if not isinstance(region, RegionIR):
        raise ModelError("portable SolidCraft Extrude IR requires RegionIR")

    try:
        pick = _region_interior_point(sketch, region)
    except ValueError as exc:
        raise ModelError(str(exc)) from exc

    commands = [_solidcraft_sketch_create(sketch)]

    polygon = (
        len(sketch.profiles) == 1
        and isinstance(sketch.profiles[0], PolygonProfileIR)
    )
    if polygon:
        if node.direction != "symmetric":
            raise ModelError(
                "portable SolidCraft PolygonProfileIR currently requires "
                "symmetric extrusion"
            )
        profile = sketch.profiles[0]
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
        commands.append(
            _command(
                "sketch.line",
                points=[
                    [command_value(value) for value in point]
                    for point in points
                ],
                closed=True,
                ids=ids,
            )
        )
    else:
        if node.direction not in ("positive", "negative"):
            raise ModelError(
                "portable SolidCraft circle Extrude IR requires "
                "positive or negative direction"
            )
        for profile in sketch.profiles:
            if not isinstance(profile, CircleProfileIR):
                raise ModelError(
                    "portable SolidCraft Extrude IR requires one qualified "
                    "profile family"
                )
            if tuple(profile.center) != (0, 0):
                raise ModelError(
                    "portable SolidCraft CircleProfileIR currently requires "
                    "origin center"
                )
            _require_positive(profile.diameter, "circle diameter")
            commands.append(
                _command(
                    "sketch.circle.center",
                    center=[
                        command_value(value)
                        for value in profile.center
                    ],
                    diameter=command_value(profile.diameter),
                )
            )

    _require_positive(node.distance, "sketch extrusion distance")
    commands.append(_command("sketch.finish"))

    extrude = {
        "body_name": name,
        "direction": node.direction,
        "distance": command_value(node.distance),
    }
    if len(sketch.profiles) > 1:
        extrude["profiles"] = [{"point": [pick[0], pick[1]]}]
        extrude["exact_regions"] = True
    commands.append(_command("solid.extrude", **extrude))
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


def _revolve_commands(model: ModelIR, node: RevolveIR, name: str) -> list[dict]:
    """Lower semantic Sketch/Profile + Revolve IR without raw Shape parsing."""
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
    revolve = {
        "sketch": sketch.name,
        "axis": _solidcraft_axis(node.axis),
        "angle": _role_command_value(model, node.angle, "angle"),
    }
    if node.operation == "new_body":
        if node.target is not None:
            raise ModelError("new-body RevolveIR must not have a target")
        revolve["body_name"] = name
    elif node.operation == "cut":
        if (
            not isinstance(node.target, PlacementIR)
            or not isinstance(node.target.primitive, BoxIR)
        ):
            raise ModelError(
                "portable SolidCraft Revolve cut currently requires a Box target"
            )
        revolve["operation"] = "cut"
        revolve["targets"] = [name]
    else:
        raise ModelError(
            f"unsupported portable SolidCraft Revolve operation {node.operation!r}"
        )

    return [
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


def _chamfer_commands(node: ChamferIR, name: str) -> list[dict]:
    _require_positive(node.distance, "chamfer distance")
    if node.distance2 is not None:
        _require_positive(node.distance2, "chamfer distance2")
    if node.flip and node.distance2 is None:
        raise ModelError("portable SolidCraft ChamferIR flip requires distance2")

    if isinstance(node.base, PlacementIR):
        if not isinstance(node.base.primitive, BoxIR):
            raise ModelError(
                "portable SolidCraft ChamferIR placement base requires BoxIR"
            )
        base_commands = [_box_command(node.base, name)]
    elif isinstance(node.base, ExtrudeIR):
        if node.distance2 is not None or node.flip:
            raise ModelError(
                "portable SolidCraft asymmetric ChamferIR requires BoxIR"
            )
        base_commands = _extrude_commands(node.base, name)
    else:
        raise ModelError(
            "portable SolidCraft ChamferIR has unsupported typed base"
        )

    topology, edges = _face_boundary_commands(
        node.edges,
        name,
        prior=base_commands,
    )
    chamfer = {
        "body": name,
        "distance": command_value(node.distance),
        "edges": edges,
    }
    if node.distance2 is not None:
        chamfer["distance2"] = command_value(node.distance2)
    if node.flip:
        chamfer["flip"] = True

    return [
        *base_commands,
        *topology,
        _command("solid.chamfer", **chamfer),
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


def _body_commands(model: ModelIR, node: BodyIR, name: str) -> list[dict]:
    """Lower one typed semantic body history without re-reading Shape.data."""
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
        return _extrude_commands(node, name)

    if isinstance(node, BooleanIR):
        return _boolean_commands(node, name)

    if isinstance(node, HoleIR):
        return _hole_commands(model, node, name)

    if isinstance(node, FilletIR):
        return _fillet_commands(node, name)

    if isinstance(node, RevolveIR):
        base_commands = []
        if node.operation == "cut":
            if (
                not isinstance(node.target, PlacementIR)
                or not isinstance(node.target.primitive, BoxIR)
            ):
                raise ModelError(
                    "portable SolidCraft Revolve cut currently requires a Box target"
                )
            base_commands = [_box_command(node.target, name)]
        return [
            *base_commands,
            *_revolve_commands(model, node, name),
        ]

    if isinstance(node, ChamferIR):
        return _chamfer_commands(node, name)

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


def compile_ir_with_dependencies(model: ModelIR, name: str):
    """Lower one normalized Forge model to SolidCraft native intent."""
    if not isinstance(model, ModelIR):
        raise TypeError("SolidCraft backend requires Forge ModelIR")
    if not name or not name.isidentifier():
        raise ModelError("the model name must be a valid identifier")

    if isinstance(model.root, LegacyShapeIR):
        return _compile_shape_legacy_with_dependencies(
            model.root.shape,
            name,
        )

    commands = _portable_commands(model, name)
    if model.configuration is not None:
        commands = _portable_configuration_commands(
            model,
            model.configuration,
            commands,
        )
    plain = _plain_command_value(commands)
    document = (
        replay_document(plain)
        if any("bind" in command for command in plain)
        else {"commands": plain}
    )
    return document, _native_dependencies(commands)


def compile_ir(model: ModelIR, name: str) -> dict:
    return compile_ir_with_dependencies(model, name)[0]


__all__ = ["compile_ir", "compile_ir_with_dependencies"]
