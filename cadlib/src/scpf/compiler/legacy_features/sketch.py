"""Legacy explicit and attached Sketch feature lowering."""

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


def _explicit_sketch_commands(
    shape,
    original,
    feature,
    name,
    *,
    face_query_index=None,
    sketch_index=1,
):
    """Compile an explicitly authored named sketch and its extrusion."""
    (
        sketch_name,
        target,
        parent_anchor,
        plane_info,
        profiles,
        distance,
        direction,
        sketch_operations,
        profile_picks,
        exact_regions,
    ) = feature.data
    plane_name, sketch_origin, sketch_rotation = plane_info
    if target != original:
        raise ModelError("explicit Sketch must target the body being modified")
    if shape.kind not in ("union", "difference"):
        raise ModelError("explicit Sketch extrusion must be added or subtracted")

    if plane_name is not None:
        if sketch_origin is not None or sketch_rotation is not None:
            plane = dict(
                plane=_sketch_plane_frame(
                    plane_name,
                    origin=sketch_origin,
                    rotation=sketch_rotation,
                ),
                name=sketch_name,
            )
        else:
            plane = dict(plane=plane_name, name=sketch_name)
        relative_origin = (0, 0)
        commands = [_command("sketch.create", **plane)]
    else:
        if parent_anchor is Anchor.TOP:
            if face_query_index is None:
                raise ModelError("attached TOP Sketch needs a face query index")
            point_var = f"$face_point_{face_query_index}"
            index_var = f"$face_index_{face_query_index}"
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
            plane = dict(
                plane={
                    "face": point_var,
                    "body": name,
                    "index": index_var,
                },
                project_edges=False,
                name=sketch_name,
            )
            relative_origin = (0, 0)
            commands = [face_query, _command("sketch.create", **plane)]
        else:
            try:
                (width, depth), (x, y, z), thickness = _base_rectangle(target)
            except ValueError as exc:
                raise ModelError(
                    "BOTTOM/CENTER attached Sketch currently requires "
                    "a rectangular solid"
                ) from exc
            if thickness is None:
                raise ModelError(
                    "BOTTOM/CENTER attached Sketch currently requires "
                    "a rectangular solid"
                )
            if parent_anchor is Anchor.BOTTOM:
                plane_z = z
            elif parent_anchor is Anchor.INNER_BOTTOM:
                wall = _shell_thickness(target)
                if wall is None:
                    raise ModelError("Anchor.INNER_BOTTOM requires a shelled body")
                plane_z = _combine(z, wall)
            elif parent_anchor is Anchor.CENTER:
                plane_z = _combine(z, half(thickness))
            else:
                raise ModelError("unsupported explicit Sketch anchor")

            plane = dict(plane="XY", name=sketch_name)
            if pv(plane_z):
                plane["offset"] = command_value(plane_z)
            center_x, center_y, _ = _base_rectangle_center(target)
            relative_origin = (center_x, center_y)
            commands = [_command("sketch.create", **plane)]

    referenced_sources = {
        id(operation.data[0])
        for operation in sketch_operations
        if operation.kind in ("sketch_pattern_rectangular", "sketch_mirror")
    }
    profile_variables = {
        id(profile): f"$sketch_{sketch_index}_profile_{index}"
        for index, (profile, _anchor, _offset) in enumerate(profiles, start=1)
        if id(profile) in referenced_sources
    }
    operation_variables = {
        id(operation): f"$sketch_{sketch_index}_operation_{index}"
        for index, operation in enumerate(sketch_operations, start=1)
    }

    def append_profile(command, profile):
        variable = profile_variables.get(id(profile))
        if variable is not None:
            command.setdefault("bind", {})[variable] = "curves"
        commands.append(command)

    def source_variable(source):
        variable = profile_variables.get(id(source))
        if variable is None:
            variable = operation_variables.get(id(source))
        if variable is None:
            raise ModelError(
                "sketch pattern/mirror source is not available in this Sketch"
            )
        return variable

    for profile_index, (profile, profile_anchor, offset) in enumerate(
        profiles, start=1
    ):
        ox = _combine(relative_origin[0], offset[0])
        oy = _combine(relative_origin[1], offset[1])

        if profile.kind == "circle":
            if profile_anchor not in (None, Anchor.CENTER):
                raise ModelError("Circle2D sketch anchor must be CENTER")
            diameter = profile.data[0]
            _require_positive(diameter, "sketch circle diameter")
            append_profile(
                _command(
                    "sketch.circle.center",
                    center=[command_value(ox), command_value(oy)],
                    diameter=command_value(diameter),
                ),
                profile,
            )
            continue

        if profile.kind in ("rectangle", "rounded_rectangle"):
            rectangle_width, rectangle_height = profile.data[:2]
            _require_positive(rectangle_width, "sketch rectangle width")
            _require_positive(rectangle_height, "sketch rectangle height")
            if profile_anchor is Anchor.CENTER:
                x0 = _combine(ox, -half(rectangle_width))
                y0 = _combine(oy, -half(rectangle_height))
                x1 = _combine(ox, half(rectangle_width))
                y1 = _combine(oy, half(rectangle_height))
            else:
                x0, y0 = ox, oy
                x1 = _combine(ox, rectangle_width)
                y1 = _combine(oy, rectangle_height)
            params = dict(
                p0=[command_value(x0), command_value(y0)],
                p1=[command_value(x1), command_value(y1)],
            )
            if profile.kind == "rounded_rectangle":
                radius = profile.data[2]
                _require_positive(radius, "sketch rounded rectangle radius")
                if pv(radius) * 2 >= min(
                        pv(rectangle_width), pv(rectangle_height)):
                    raise ModelError("rounded rectangle radius exceeds half the shorter side")
                params["radius"] = command_value(radius)
                command = "sketch.rectangle.rounded"
            else:
                command = "sketch.rectangle.two_point"
            append_profile(_command(command, **params), profile)
            continue

        if profile.kind == "polygon":
            if profile_anchor is not None:
                raise ModelError(
                    "Polygon2D uses authored sketch coordinates; "
                    "semantic CENTER is not supported yet"
                )
            append_profile(
                _polygon_profile_command(
                    profile,
                    plane=plane_name or "XY",
                    offset=(ox, oy),
                ),
                profile,
            )
            continue

        if profile.kind == "text":
            if profile_anchor is not None:
                raise ModelError(
                    "Text2D uses its native insertion point; "
                    "semantic CENTER is not supported yet"
                )
            text, height, font = profile.data
            _require_positive(height, "sketch text height")
            append_profile(
                _command(
                    "sketch.text", text=text,
                    at=[command_value(ox), command_value(oy)],
                    height=command_value(height), font=font,
                ),
                profile,
            )
            continue

        if profile.kind == "connected_profile":
            if profile_anchor is not None:
                raise ModelError(
                    "connected profiles use authored sketch coordinates"
                )
            if id(profile) in referenced_sources:
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            connected, _meta = compile_connected_profile(
                profile,
                offset=(ox, oy),
            )
            commands.extend(connected)
            continue

        if profile.kind in (
            "slot_center_to_center",
            "slot_overall",
            "slot_center_point",
            "slot_arc_three_point",
            "slot_arc_center",
        ):
            if profile_anchor is not None:
                raise ModelError(
                    "native Slot profiles use authored sketch coordinates"
                )

            def slot_intent(point):
                return (
                    _combine(ox, point[0]),
                    _combine(oy, point[1]),
                )

            def direct_slot_point(point):
                values = [
                    command_value(value)
                    for value in slot_intent(point)
                ]
                if any(isinstance(value, str) for value in values):
                    raise ModelError(
                        "native Slot point coordinates currently require "
                        "fixed values"
                    )
                return values

            def seed_point(intent):
                return [pv(intent[0]), pv(intent[1])]

            def same_intent(left, right):
                return command_value(left) == command_value(right)

            def emit_parametric_straight_slot(
                command_name,
                point_key_a,
                point_a,
                point_key_b,
                point_b,
                width,
                *,
                center_point=False,
            ):
                intent_a = slot_intent(point_a)
                intent_b = slot_intent(point_b)
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

                delta = _dim_abs(
                    _dim_sub(intent_b[axis], intent_a[axis])
                )
                if center_point:
                    # SolidCraft 0.45 defines center-point Slot length as
                    # the complete straight centre-line length, while authored
                    # end is one half-length away from center.
                    delta = delta * 2

                middle = (
                    intent_a
                    if center_point
                    else (
                        midpoint(intent_a[0], intent_b[0]),
                        midpoint(intent_a[1], intent_b[1]),
                    )
                )

                params = {
                    point_key_a: seed_point(intent_a),
                    point_key_b: seed_point(intent_b),
                    "width": command_value(width),
                }
                centre_line = (
                    f"$sketch_{sketch_index}_slot_"
                    f"{profile_index}_centre_line"
                )
                middle_point = (
                    f"$sketch_{sketch_index}_slot_"
                    f"{profile_index}_middle"
                )

                dimensioned = _command(
                    "sketch.draw.dimensioned",
                    command=command_name,
                    params=params,
                    dimensions={"length": command_value(delta)},
                )
                dimensioned["bind"] = {
                    centre_line: "centre_line",
                    middle_point: "middle",
                }
                append_profile(dimensioned, profile)

                commands.append(_command(
                    "sketch.constraint.horizontal_vertical",
                    line=centre_line,
                    mode=mode,
                ))
                commands.append(_command(
                    "sketch.dimension",
                    entities=["origin", middle_point],
                    type="horizontal",
                    value=command_value(_dim_abs(middle[0])),
                ))
                commands.append(_command(
                    "sketch.dimension",
                    entities=["origin", middle_point],
                    type="vertical",
                    value=command_value(_dim_abs(middle[1])),
                ))

            if profile.kind == "slot_center_to_center":
                p0, p1, width = profile.data
                intents = (slot_intent(p0), slot_intent(p1))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.center_to_center",
                        "p0",
                        p0,
                        "p1",
                        p1,
                        width,
                    )
                    continue
                params = dict(
                    p0=direct_slot_point(p0),
                    p1=direct_slot_point(p1),
                    width=command_value(width),
                )
                command = "sketch.slot.center_to_center"
            elif profile.kind == "slot_overall":
                p0, p1, width = profile.data
                intents = (slot_intent(p0), slot_intent(p1))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.overall",
                        "p0",
                        p0,
                        "p1",
                        p1,
                        width,
                    )
                    continue
                params = dict(
                    p0=direct_slot_point(p0),
                    p1=direct_slot_point(p1),
                    width=command_value(width),
                )
                command = "sketch.slot.overall"
            elif profile.kind == "slot_center_point":
                center, end, width = profile.data
                intents = (slot_intent(center), slot_intent(end))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.center_point",
                        "center",
                        center,
                        "end",
                        end,
                        width,
                        center_point=True,
                    )
                    continue
                params = dict(
                    center=direct_slot_point(center),
                    end=direct_slot_point(end),
                    width=command_value(width),
                )
                command = "sketch.slot.center_point"
            elif profile.kind == "slot_arc_three_point":
                start, through, end, width = profile.data
                params = dict(
                    start=direct_slot_point(start),
                    through=direct_slot_point(through),
                    end=direct_slot_point(end),
                    width=command_value(width),
                )
                command = "sketch.slot.arc_three_point"
            else:
                center, start, end, sweep, width = profile.data
                params = dict(
                    center=direct_slot_point(center),
                    start=direct_slot_point(start),
                    width=command_value(width),
                )
                if end is not None:
                    params["end"] = direct_slot_point(end)
                else:
                    params["sweep"] = sweep
                command = "sketch.slot.arc_center"

            append_profile(_command(command, **params), profile)
            continue

        raise ModelError(
            "explicit Sketch supports Circle2D, Rectangle2D, RoundedRectangle2D, "
            "Polygon2D, connected profiles, Text2D or native Slot*2D profiles"
        )

    for operation in sketch_operations:
        variable = operation_variables[id(operation)]
        if operation.kind == "sketch_pattern_rectangular":
            (
                source,
                count,
                spacing,
                dir1,
                count2,
                spacing2,
                dir2,
                alignment,
                alignment2,
                reversed1,
                reversed2,
            ) = operation.data
            params = {
                "entities": source_variable(source),
                "count": command_value(count),
                "spacing": command_value(spacing),
                "dir": list(dir1),
            }
            has_second_direction = (
                pv(count2) != 1
                or bool(parameters_in(count2))
            )
            if has_second_direction:
                params["count2"] = command_value(count2)
                if spacing2 is not None:
                    params["spacing2"] = command_value(spacing2)
                if dir2 is not None:
                    params["dir2"] = list(dir2)
            if alignment != "right":
                params["alignment"] = alignment
            if has_second_direction and alignment2 != "right":
                params["alignment2"] = alignment2
            if reversed1:
                params["reversed"] = True
            if has_second_direction and reversed2:
                params["reversed2"] = True
            command = _command("sketch.pattern.rectangular", **params)
        elif operation.kind == "sketch_mirror":
            source, line = operation.data
            command = _command(
                "sketch.mirror",
                entities=source_variable(source),
                line=line,
            )
        else:
            raise ModelError(
                f"unsupported explicit Sketch operation {operation.kind}"
            )
        if operation.kind == "sketch_pattern_rectangular":
            command["bind"] = {
                variable: {
                    "field": "curves",
                    "prepend": source_variable(source),
                }
            }
        else:
            command["bind"] = {variable: "curves"}
        commands.append(command)

    commands.append(_command("sketch.finish"))

    extrude = dict(
        operation="join" if shape.kind == "union" else "cut",
        targets=[name],
        name=sketch_name,
    )
    if distance is Depth.THROUGH_ALL:
        if shape.kind != "difference":
            raise ModelError("Depth.THROUGH_ALL is only supported for Sketch cuts")
        extrude["through_all"] = True
        extrude["direction"] = direction
    else:
        extrude["distance"] = command_value(distance)
        extrude["direction"] = direction

    extrude.update(
        _extrude_profile_params(profile_picks, exact_regions)
    )
    commands.append(_command("solid.extrude", **extrude))
    return commands
