"""SolidCraft lowering for holes, plastic features and feature patterns."""
from __future__ import annotations

from fnmatch import fnmatchcase
from math import isfinite

from ...compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from ...core import (
    Expression,
    Parameter,
    _DirectionSelector,
    _dim_abs,
    _dim_add,
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
from ...ir import (
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
    NamedFeatureIR,
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
    TranslationIR,
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
from ...placement import _combine
from ...replay import replay_document
from ...scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


from .common import _require_positive, _command, _role_command_value
from .sketch import _solidcraft_axis

_AUTO_TYPED_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.extrude": "Extrude",
    "solid.hole": "Hole",
}


def _body_commands(*args, **kwargs):
    from .dispatch import body_commands
    return body_commands(*args, **kwargs)


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
