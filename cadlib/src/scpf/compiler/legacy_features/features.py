"""Legacy Hole and plastic-feature lowering."""

from math import isfinite
from fnmatch import fnmatchcase
from ...core import (
    Shape,
    Edges,
    Faces,
    Depth,
    Anchor,
    Parameter,
    _DirectionSelector,
    _ProfileEdgeSelection,
    _FaceBoundarySelection,
    _dim_add,
    _dim_abs,
    _dim_sub,
    _cylinder_base_from_anchor,
    half,
    midpoint,
    _pv as pv,
    command_value,
    number_text,
    parameters_in,
    _hole_spec,
)
from ..errors import ModelError, _require_positive
from ..legacy import _command, _collect, _param_commands
from ...placement import (
    _anchored_features,
    _base_rectangle,
    _base_rectangle_center,
    _combine,
    _shell_thickness,
)
from ...sketches import (
    compile_base,
    compile_connected_profile,
    compile_open_chain,
    compile_open_chain_with_curves,
    compile_standalone_sketch,
    _extrude_profile_params,
    _polygon_profile_command,
    _sketch_plane_frame,
)


def _hole_commands(feature, position, name, refs=None):
    """Compile one explicitly positioned Hole-family feature."""
    if feature.kind != "hole":
        raise ModelError("native hole operation requires a Hole-family feature")
    spec = _hole_spec(feature)
    hole_type = spec["type"]
    diameter = spec["diameter"]
    depth = spec["depth"]
    direction = spec["direction"]
    counterbore_d = spec["counterbore_diameter"]
    counterbore_depth = spec["counterbore_depth"]
    countersink_d = spec["countersink_diameter"]
    countersink_angle = spec["countersink_angle"]
    thread = spec["thread"]
    hand = spec["hand"]
    thread_depth = spec["thread_depth"]
    modeled = spec["modeled"]
    ease_out = spec["ease_out"]

    point = tuple(position)
    concrete_point = [pv(v) for v in point]
    if not all(isfinite(v) for v in concrete_point):
        raise ModelError("hole position must be finite")

    direction_vector = (
        _vector(direction, "hole direction") if direction is not None else None
    )

    params = {
        "position": (
            [command_value(v) for v in point]
            if direction_vector is not None
            else [pv(v) for v in point]
        ),
        "targets": [name],
    }
    if diameter is not None:
        _require_positive(diameter, "hole diameter")
        params["diameter"] = command_value(diameter)
    if depth is not Depth.THROUGH_ALL:
        _require_positive(depth, "hole depth")
        params["depth"] = command_value(depth)
    if direction_vector is not None:
        params["direction"] = direction_vector
    if refs:
        params["references"] = refs

    if hole_type == "simple":
        pass
    elif hole_type == "counterbore":
        _require_positive(counterbore_d, "counterbore diameter")
        _require_positive(counterbore_depth, "counterbore depth")
        if pv(counterbore_d) <= pv(diameter):
            raise ModelError(
                "counterbore diameter must exceed hole diameter"
            )
        params.update(
            type="counterbore",
            cb_diameter=command_value(counterbore_d),
            cb_depth=command_value(counterbore_depth),
        )
    elif hole_type == "countersink":
        _require_positive(countersink_d, "countersink diameter")
        if pv(countersink_d) <= pv(diameter):
            raise ModelError(
                "countersink diameter must exceed hole diameter"
            )
        angle = pv(countersink_angle)
        if not isfinite(angle) or angle <= 0 or angle >= 180:
            raise ModelError(
                "countersink angle must be between 0 and 180 degrees"
            )
        params.update(
            type="countersink",
            cs_diameter=command_value(countersink_d),
            cs_angle=command_value(countersink_angle),
        )
    elif hole_type == "threaded":
        params["thread"] = thread
        if hand != "right":
            params["hand"] = hand
        if thread_depth is not None:
            _require_positive(thread_depth, "thread depth")
            params["thread_depth"] = command_value(thread_depth)
        if modeled:
            params["modeled"] = True
        if ease_out is not None:
            params["ease_out"] = (
                command_value(ease_out)
                if not isinstance(ease_out, str)
                else ease_out
            )
    else:
        raise ModelError(f"unsupported Hole-family type {hole_type}")

    return [_command("solid.hole", **params)]


_CARDINAL_FACE_NORMAL = {
    Faces.TOP: [0, 0, 1],
    Faces.BOTTOM: [0, 0, -1],
    Faces.LEFT: [-1, 0, 0],
    Faces.RIGHT: [1, 0, 0],
    Faces.FRONT: [0, -1, 0],
    Faces.BACK: [0, 1, 0],
}


def _vector(values, label):
    concrete = [pv(v) for v in values]
    if len(concrete) != 3 or not all(isfinite(v) for v in concrete):
        raise ModelError(f"{label} must be a finite 3D direction")
    if concrete == [0, 0, 0]:
        raise ModelError(f"{label} cannot be the zero vector")
    return concrete


def _plastic_feature_command(feature, position, name):
    """Compile one native SolidCraft plastic feature at an explicit face pick."""
    point = [pv(v) for v in position]
    if not all(isfinite(v) for v in point):
        raise ModelError("plastic feature position must be finite")

    if feature.kind == "lip":
        width, height = feature.data
        _require_positive(width, "lip width")
        _require_positive(height, "lip height")
        return _command(
            "plastic.lip",
            face=point,
            width=command_value(width),
            height=command_value(height),
            body=name,
        )

    if feature.kind == "snap_fit":
        length, thickness, width, catch_depth, catch_length, hook, direction = feature.data
        for value, label in (
            (length, "snap-fit length"),
            (thickness, "snap-fit thickness"),
            (width, "snap-fit width"),
            (catch_depth, "snap-fit catch depth"),
            (catch_length, "snap-fit catch length"),
        ):
            _require_positive(value, label)
        params = dict(
            position=point,
            hook=_vector(hook, "snap-fit hook"),
            length=command_value(length),
            thickness=command_value(thickness),
            width=command_value(width),
            catch_depth=command_value(catch_depth),
            catch_length=command_value(catch_length),
            body=name,
        )
        if direction is not None:
            params["direction"] = _vector(direction, "snap-fit direction")
        return _command("plastic.snap_fit", **params)

    if feature.kind == "boss":
        diameter, height, hole_diameter, direction = feature.data
        _require_positive(diameter, "boss diameter")
        _require_positive(height, "boss height")
        params = dict(
            position=point,
            diameter=command_value(diameter),
            height=command_value(height),
            body=name,
        )
        if hole_diameter is not None:
            _require_positive(hole_diameter, "boss hole diameter")
            params["hole_diameter"] = command_value(hole_diameter)
        if direction is not None:
            params["direction"] = _vector(direction, "boss direction")
        return _command("plastic.boss", **params)

    if feature.kind == "rest":
        width, height, length, along, direction = feature.data
        _require_positive(width, "rest width")
        _require_positive(height, "rest height")
        params = dict(
            position=point,
            width=command_value(width),
            height=command_value(height),
            body=name,
        )
        if length is not None:
            _require_positive(length, "rest length")
            params["length"] = command_value(length)
        if along is not None:
            params["along"] = _vector(along, "rest along")
        if direction is not None:
            params["direction"] = _vector(direction, "rest direction")
        return _command("plastic.rest", **params)

    raise ModelError(f"unsupported plastic feature {feature.kind}")


def _attached_hole_commands(child, target, parent_anchor, resolved, name):
    """Compile Hole intent as one editable sketch plus one cut feature."""
    feature = child
    if feature.kind != "hole":
        raise ModelError("expected Hole feature")
    if parent_anchor is not Anchor.TOP:
        raise ModelError("Hole.attach() currently starts drilling from Anchor.TOP")

    spec = _hole_spec(feature)
    hole_type = spec["type"]
    diameter = spec["diameter"]
    depth = spec["depth"]
    hole_direction = spec["direction"]
    _require_positive(diameter, "hole diameter")
    if hole_type != "simple" or hole_direction is not None:
        raise ModelError(
            "non-simple or directional Hole-family features currently require explicit .at() placement"
        )
    (_, _), (_, _, origin_z), thickness = _base_rectangle(target)
    base_top = thickness if pv(origin_z) == 0 else _combine(origin_z, thickness)
    entry_z = base_top
    on_base_top = True

    # If the current body ends in a centered Cylinder attached to its top,
    # the next Hole starts on that boss top. Keep the symbolic height so the
    # generated Bore sketch remains parametrically tied to the base thickness.
    if target.kind == "union":
        previous, attached = target.data
        if attached.kind == "anchored":
            boss, boss_parent, boss_parent_anchor, boss_child_anchor, boss_offset = attached.data
            if (boss.kind == "cylinder" and boss_parent == previous
                    and boss_parent_anchor is Anchor.TOP
                    and boss_child_anchor is Anchor.BOTTOM
                    and all(pv(v) == 0 for v in boss_offset)):
                boss_height, _, boss_axis, _boss_origin = boss.data
                if boss_axis != "Z":
                    raise ModelError("attached boss Cylinder must use Axis.Z")
                entry_z = (base_top + boss_height
                           if isinstance(boss_height, (int, float))
                           else _combine(base_top, boss_height))
                on_base_top = False

    if depth is Depth.THROUGH_ALL:
        if on_base_top:
            # Preserve the editable Sample Plate convention: XY/base-plane
            # sketch and positive cut through the plate thickness.
            sketch_z = origin_z
            distance = thickness
            direction = "positive"
        else:
            # A bore starting on a joined boss is sketched at its entry face
            # and cuts back through the complete current height.
            sketch_z = entry_z
            distance = (entry_z if pv(origin_z) == 0
                        else _combine(entry_z, -pv(origin_z)))
            direction = "negative"
    else:
        _require_positive(depth, "hole depth")
        sketch_z = entry_z
        distance = depth
        direction = "negative"

    label = "Bore" if not on_base_top else "Hole"
    plane = {"plane": "XY", "name": label}
    if pv(sketch_z):
        plane["offset"] = command_value(sketch_z)

    operations = [_command("sketch.create", **plane)]
    for primitive, position, _refs in resolved:
        hole_diameter = _hole_spec(primitive)["diameter"]
        operations.append(_command(
            "sketch.circle.center",
            center=position[:2],
            diameter=command_value(hole_diameter),
        ))
    operations.extend([
        _command("sketch.finish"),
        _command("solid.extrude",
                 distance=command_value(distance),
                 direction=direction,
                 operation="cut",
                 targets=[name],
                 name=label),
    ])
    return operations


def _attached_commands(shape, original, feature, name, *, feature_name=None):
    child, target, parent_anchor, child_anchor, offset = feature.data
    if target != original:
        raise ModelError("attached feature must target the body being modified")
    try:
        resolved = _anchored_features(feature)
    except (ValueError, TypeError) as exc:
        raise ModelError(str(exc)) from exc

    attached_primitive = child
    if attached_primitive.kind == "hole":
        return _attached_hole_commands(
            child, target, parent_anchor, resolved, name)
    if attached_primitive.kind in ("lip", "snap_fit", "boss", "rest"):
        if shape.kind != "union":
            raise ModelError("plastic features are added with +")
        return [
            _plastic_feature_command(primitive, position, name)
            for primitive, position, _refs in resolved
        ]

    operations = []
    for primitive, position, refs in resolved:
        height, diameter, axis, _constructor_anchor = primitive.data
        _require_positive(height, "cylinder height")
        _require_positive(diameter, "cylinder diameter")
        if axis != "Z":
            raise ModelError("attached Cylinder must use Axis.Z")
        params = dict(
            height=command_value(height),
            diameter=command_value(diameter),
            base=position,
            axis=axis,
            operation="join" if shape.kind == "union" else "cut",
            targets=[name],
        )
        if refs:
            params["references"] = refs
        if feature_name is not None:
            params["name"] = feature_name
        operations.append(_command("solid.cylinder", **params))
    return operations
