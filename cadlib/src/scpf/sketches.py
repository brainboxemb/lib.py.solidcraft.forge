"""Native SolidCraft sketch construction for primitive CAD profiles.

Each supported base shape returns its command list plus simple shape metadata.
Feature operations (Hole, Fillet, join, cut) are handled separately.
"""
from math import cos, isfinite, radians, sin
from .core import (
    Shape,
    Anchor,
    _NativeExpression,
    _native_expression,
    _native_dependencies,
    _box_corner_from_anchor,
    command_value,
    half,
    _pv as pv,
)
from .placement import _base_rectangle


def _combine_dimension(a, b):
    """Preserve native expressions when adding an offset to a parameter."""
    if isinstance(a, (int, float)) and a == 0:
        return b
    if isinstance(b, (int, float)) and b == 0:
        return a
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b
    left = command_value(a)
    right = command_value(b)
    return _native_expression(
        f"({left}) + ({right})",
        tuple(sorted(_native_dependencies((left, right)))),
    )

from .compiler import ModelError, _command, _require_positive
from .csg import _half

def _extrude_profile_params(profile_picks, exact_regions):
    """Lower normalized Sketch profile picks to SolidCraft extrude parameters."""
    if profile_picks is None:
        return {}
    params = {
        "profiles": [
            {"point": [x, y]}
            for x, y in profile_picks
        ],
    }
    if exact_regions:
        params["exact_regions"] = True
    return params


def _polygon_profile_command(profile, *, plane, offset=(0, 0)):
    """Lower one Polygon2D profile to one closed native sketch line."""

    if profile.kind != "polygon":
        raise ModelError("expected a Polygon2D profile")
    points, profile_plane, ids = profile.data
    if profile_plane != plane:
        raise ModelError("Polygon2D plane must match Sketch plane")

    ox, oy = offset
    shifted = [
        (
            _combine_dimension(ox, point[0]),
            _combine_dimension(oy, point[1]),
        )
        for point in points
    ]
    concrete = [tuple(pv(v) for v in point) for point in shifted]
    if not all(isfinite(v) for point in concrete for v in point):
        raise ModelError("non-finite polygon coordinate")
    if len(set(concrete)) != len(concrete):
        raise ModelError("duplicate polygon vertices")
    if any(a == b for a, b in zip(concrete, concrete[1:] + concrete[:1])):
        raise ModelError("zero-length polygon edge")

    return _command(
        "sketch.line",
        points=[
            [command_value(value) for value in point]
            for point in shifted
        ],
        closed=True,
        ids=list(ids) if ids is not None else
        [chr(ord("a") + i) for i in range(len(points))],
    )


def compile_connected_profile(profile, *, offset=(0, 0), assign_ids=False):
    """Lower one declarative mixed line/arc profile into native sketch commands."""

    if profile.kind != "connected_profile":
        raise ModelError("expected a connected_profile")
    start, segments = profile.data
    ox, oy = offset

    def point(value):
        return [
            command_value(_combine_dimension(ox, value[0])),
            command_value(_combine_dimension(oy, value[1])),
        ]

    commands = []
    line_index = 0
    arc_index = 0
    for segment in segments:
        kind = segment[0]
        if kind == "line":
            _kind, segment_start, end = segment
            line_index += 1
            params = {
                "points": [point(segment_start), point(end)],
                "connect": True,
            }
            if assign_ids:
                params["ids"] = [f"l{line_index}"]
            commands.append(_command("sketch.line", **params))
            continue
        if kind == "arc_three_point":
            _kind, segment_start, end, through = segment
            arc_index += 1
            params = {
                "start": point(segment_start),
                "end": point(end),
                "through": point(through),
                "connect": True,
            }
            if assign_ids:
                params["id"] = f"a{arc_index}"
            commands.append(_command("sketch.arc.three_point", **params))
            continue
        if kind == "arc_center_point":
            _kind, segment_start, end, center, clockwise = segment
            arc_index += 1
            params = {
                "center": point(center),
                "start": point(segment_start),
                "end": point(end),
                "clockwise": clockwise,
                "connect": True,
            }
            if assign_ids:
                params["id"] = f"a{arc_index}"
            commands.append(_command("sketch.arc.center_point", **params))
            continue
        raise ModelError(f"unsupported connected profile segment: {kind}")

    return commands, {
        "profile": "connected",
        "profile_start": start,
        "profile_segments": segments,
    }



def _compile_open_chain(shape, *, bind_curves):
    """Lower one reusable open Sketch chain, optionally binding all curve ids."""

    if shape.kind != "sketch_open_chain":
        raise ModelError("expected a sketch_open_chain")
    sketch_name, plane, plane_offset, _start, segments = shape.data
    if plane not in ("XY", "XZ", "YZ"):
        raise ModelError("open Sketch chain requires an XY, XZ or YZ plane")

    params = {"plane": plane, "name": sketch_name}
    if plane_offset is not None:
        params["offset"] = command_value(plane_offset)
    commands = [_command("sketch.create", **params)]

    def point(value):
        return [command_value(value[0]), command_value(value[1])]

    curve_variable = None
    curve_count = 0

    def append_curve(command):
        nonlocal curve_variable, curve_count
        if bind_curves:
            curve_count += 1
            next_variable = f"$contour_curves_{curve_count}"
            if curve_variable is None:
                binding = "curves"
            else:
                binding = {
                    "field": "curves",
                    "prepend": curve_variable,
                }
            command["bind"] = {next_variable: binding}
            curve_variable = next_variable
        commands.append(command)

    previous_line_id = None
    line_count = 0
    for segment in segments:
        kind = segment[0]
        if kind == "line":
            _kind, start, end = segment
            line_count += 1
            line_id = f"l{line_count}"
            append_curve(
                _command(
                    "sketch.line",
                    points=[point(start), point(end)],
                    ids=[line_id],
                    connect=True,
                )
            )
            previous_line_id = line_id
            continue

        if kind == "arc_tangent":
            _kind, _start, end = segment
            if previous_line_id is None:
                raise ModelError(
                    "open Sketch tangent arc requires a preceding line"
                )
            append_curve(
                _command(
                    "sketch.arc.tangent",
                    start=f"{previous_line_id}.end",
                    curve=previous_line_id,
                    end=point(end),
                )
            )
            previous_line_id = None
            continue

        raise ModelError(f"unsupported open Sketch chain segment: {kind}")

    commands.append(_command("sketch.finish"))
    meta = {
        "sketch": True,
        "open_chain": True,
        "sketch_name": sketch_name,
        "sketch_plane": plane,
        "sketch_plane_offset": plane_offset if plane_offset is not None else 0,
        "segments": segments,
    }
    return commands, meta, curve_variable


def compile_open_chain(shape):
    """Lower one reusable open Sketch chain to native SolidCraft commands."""

    commands, meta, _curve_variable = _compile_open_chain(
        shape,
        bind_curves=False,
    )
    return commands, meta


def compile_open_chain_with_curves(shape):
    """Lower an open chain and bind its complete ordered native curve list."""

    commands, meta, curve_variable = _compile_open_chain(
        shape,
        bind_curves=True,
    )
    if curve_variable is None:
        raise ModelError("open Sketch chain has no curves to consume")
    return commands, meta, curve_variable

def _sketch_plane_frame(plane, *, origin=None, rotation=None):
    """Return a native world Sketch frame for an explicit plane and rotation."""

    axes = {
        "XY": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        "XZ": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "YZ": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    }
    if plane not in axes:
        raise ModelError("Sketch frame requires an XY, XZ or YZ plane")

    x_dir, y_dir = axes[plane]
    angles = rotation or (0.0, 0.0, 0.0)
    rx, ry, rz = (radians(float(value)) for value in angles)

    def rotate(vector):
        x, y, z = vector
        y, z = y * cos(rx) - z * sin(rx), y * sin(rx) + z * cos(rx)
        x, z = x * cos(ry) + z * sin(ry), -x * sin(ry) + z * cos(ry)
        x, y = x * cos(rz) - y * sin(rz), x * sin(rz) + y * cos(rz)
        return tuple(
            0.0 if abs(value) < 1e-12 else
            1.0 if abs(value - 1.0) < 1e-12 else
            -1.0 if abs(value + 1.0) < 1e-12 else
            value
            for value in (x, y, z)
        )

    return {
        "origin": [pv(value) for value in (origin or (0, 0, 0))],
        "x_dir": list(rotate(x_dir)),
        "y_dir": list(rotate(y_dir)),
    }


def compile_standalone_sketch(
    sketch_name,
    plane,
    origin,
    plane_offset,
    profiles,
    operations,
    rotation=None,
):
    """Compile one standalone Sketch without choosing its 3D operation."""
    move_operations = [
        operation
        for operation in operations
        if operation.kind == "sketch_move_points"
    ]
    if len(move_operations) != len(operations):
        raise ModelError(
            "standalone Sketch currently supports only move_points operations"
        )
    if move_operations and (
        len(profiles) != 1
        or profiles[0][0].kind != "connected_profile"
    ):
        raise ModelError(
            "sketch move_points currently requires one connected profile"
        )
    if plane not in ("XY", "XZ", "YZ"):
        raise ModelError("standalone Sketch requires an XY, XZ or YZ plane")
    if not profiles:
        raise ModelError("standalone Sketch requires at least one profile")
    if (origin is not None or rotation is not None) and plane_offset is not None:
        raise ModelError("explicit Sketch frame cannot use plane offset")

    if origin is not None or rotation is not None:
        sketch_params = {
            "plane": _sketch_plane_frame(
                plane,
                origin=origin,
                rotation=rotation,
            ),
            "name": sketch_name,
        }
    else:
        sketch_params = {"plane": plane, "name": sketch_name}
        if plane_offset is not None:
            sketch_params["offset"] = command_value(plane_offset)
    sketch = [_command("sketch.create", **sketch_params)]

    profile_meta = []
    for profile, profile_anchor, (ox, oy) in profiles:
        if profile.kind in ("rectangle", "rounded_rectangle"):
            width, depth = profile.data[:2]
            _require_positive(width, "rectangle width")
            _require_positive(depth, "rectangle depth")
            if profile_anchor is Anchor.CENTER:
                x0 = _combine_dimension(ox, -half(width))
                y0 = _combine_dimension(oy, -half(depth))
                x1 = _combine_dimension(ox, half(width))
                y1 = _combine_dimension(oy, half(depth))
            else:
                x0, y0 = ox, oy
                x1 = _combine_dimension(ox, width)
                y1 = _combine_dimension(oy, depth)
            rectangle = dict(
                p0=[command_value(x0), command_value(y0)],
                p1=[command_value(x1), command_value(y1)],
            )
            if profile.kind == "rounded_rectangle":
                radius = profile.data[2]
                _require_positive(radius, "rounded rectangle radius")
                if pv(radius) * 2 >= min(pv(width), pv(depth)):
                    raise ModelError(
                        "rounded rectangle radius exceeds half the shorter side"
                    )
                rectangle["radius"] = command_value(radius)
                command = "sketch.rectangle.rounded"
            else:
                command = "sketch.rectangle.two_point"
            sketch.append(_command(command, **rectangle))
            current_meta = {
                "profile": profile.kind,
                "width": width,
                "depth": depth,
                "origin": (x0, y0, 0),
            }
        elif profile.kind == "circle":
            (diameter,) = profile.data
            _require_positive(diameter, "circle diameter")
            if profile_anchor not in (None, Anchor.CENTER):
                raise ModelError("Circle2D sketch anchor must be CENTER")
            sketch.append(_command(
                "sketch.circle.center",
                center=[command_value(ox), command_value(oy)],
                diameter=command_value(diameter),
            ))
            current_meta = {"profile": "circle"}
        elif profile.kind == "connected_profile":
            if profile_anchor is not None:
                raise ModelError(
                    "connected profiles use authored sketch coordinates"
                )
            connected, current_meta = compile_connected_profile(
                profile,
                offset=(ox, oy),
                assign_ids=bool(move_operations),
            )
            sketch.extend(connected)
            current_meta.update(
                {
                    "sketch_plane": plane,
                    "sketch_plane_offset": (
                        plane_offset if plane_offset is not None else 0
                    ),
                }
            )
        elif profile.kind == "polygon":
            if profile_anchor is not None:
                raise ModelError(
                    "Polygon2D uses authored sketch coordinates; "
                    "semantic CENTER is not supported yet"
                )
            points, _profile_plane, ids = profile.data
            if pv(ox) or pv(oy):
                raise ModelError("standalone Polygon2D offset is not supported yet")
            sketch.append(
                _polygon_profile_command(
                    profile,
                    plane=plane,
                    offset=(ox, oy),
                )
            )
            current_meta = {
                "profile": "polygon",
                "sketch_plane": plane,
                "sketch_plane_offset": (
                    plane_offset if plane_offset is not None else 0
                ),
                "profile_points": points,
                "profile_ids": ids,
            }
        else:
            raise ModelError(
                "standalone Sketch supports Rectangle2D, RoundedRectangle2D, "
                "Circle2D, Polygon2D and connected profiles"
            )
        profile_meta.append(current_meta)

    if move_operations:
        profile = profiles[0][0]
        _start, segments = profile.data

        def same_point(left, right):
            return all(
                abs(float(pv(a)) - float(pv(b))) <= 1e-9
                for a, b in zip(left, right)
            )

        def point_ref(source):
            endpoints = []
            centres = []
            line_index = 0
            arc_index = 0
            for segment in segments:
                kind = segment[0]
                if kind == "line":
                    _kind, start, end = segment
                    line_index += 1
                    for suffix, candidate in (("start", start), ("end", end)):
                        if same_point(candidate, source):
                            endpoints.append(f"l{line_index}.{suffix}")
                    continue
                if kind == "arc_three_point":
                    _kind, start, end, _through = segment
                    arc_index += 1
                    for suffix, candidate in (("start", start), ("end", end)):
                        if same_point(candidate, source):
                            endpoints.append(f"a{arc_index}.{suffix}")
                    continue
                if kind == "arc_center_point":
                    _kind, start, end, center, _clockwise = segment
                    arc_index += 1
                    for suffix, candidate in (("start", start), ("end", end)):
                        if same_point(candidate, source):
                            endpoints.append(f"a{arc_index}.{suffix}")
                    if same_point(center, source):
                        centres.append(f"a{arc_index}.center")
                    continue
            if endpoints:
                return endpoints[0]
            if len(centres) == 1:
                return centres[0]
            if len(centres) > 1:
                raise ModelError(
                    "sketch move source matches multiple arc centres"
                )
            raise ModelError(
                f"sketch move source {tuple(source)!r} is not a connected-profile point"
            )

        for operation in move_operations:
            (moves,) = operation.data
            sketch.append(_command(
                "sketch.move_points",
                moves=[
                    {
                        "point": point_ref(source),
                        "to": [float(target[0]), float(target[1])],
                    }
                    for source, target in moves
                ],
            ))

    sketch.append(_command("sketch.finish"))
    if len(profile_meta) == 1:
        meta = profile_meta[0]
    else:
        meta = {
            "profile": "multiple",
            "profile_count": len(profile_meta),
            "sketch_plane": plane,
            "sketch_plane_offset": (
                plane_offset if plane_offset is not None else 0
            ),
        }
    return sketch, meta


def compile_base(shape, name, *, operation="new"):
    """Create or apply a native editable base feature."""
    if operation not in ("new", "join", "cut", "intersect"):
        raise ModelError(f"unsupported base operation: {operation}")
    if shape.kind in ("box", "placed_box"):
        if shape.kind == "box":
            length, width, height, box_anchor = shape.data
            origin = _box_corner_from_anchor(
                length,
                width,
                height,
                (0, 0, 0),
                box_anchor,
            )
            selector = box_anchor.vector
            if selector == (0, 0, 0):
                placement = {"center": [0, 0, 0]}
            elif selector == (0, 0, -1):
                # Explicit BOTTOM keeps the bottom-face centre at Z=0.
                placement = {
                    "corner": [
                        _half(length, True),
                        _half(width, True),
                        0,
                    ]
                }
            else:
                placement = {
                    "corner": [
                        command_value(value)
                        for value in origin
                    ]
                }
        else:
            (length, width), origin, height = _base_rectangle(shape)
            placement = {
                "corner": [
                    command_value(value)
                    for value in origin
                ]
            }

        _require_positive(length, "box length")
        _require_positive(width, "box width")
        _require_positive(height, "box height")
        # Native 3D primitives must not synthesize a 2D sketch.
        steps = [
            _command(
                "solid.box",
                length=command_value(length),
                width=command_value(width),
                height=command_value(height),
                **placement,
                body_name=name,
            ),
        ]
        return steps, {
            "profile": "rectangle",
            "primitive": "box",
            "width": length,
            "depth": width,
            "thickness": height,
            "origin": origin,
        }

    if shape.kind == "sketch_base_extrusion":
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
        _require_positive(distance, "sketch extrusion distance")
        sketch, meta = compile_standalone_sketch(
            sketch_name,
            plane,
            origin,
            plane_offset,
            profiles,
            operations,
            rotation,
        )
        meta["thickness"] = distance
        if meta.get("profile") == "polygon":
            meta["extrusion_direction"] = direction

        extrude = dict(
            distance=command_value(distance),
            direction=direction,
        )
        if operation == "new":
            extrude["body_name"] = name
        else:
            extrude["operation"] = operation
            extrude["targets"] = [name]
        extrude.update(
            _extrude_profile_params(profile_picks, exact_regions)
        )
        sketch.append(_command("solid.extrude", **extrude))
        return sketch, meta

    if shape.kind == "sketch_base_revolve":
        (
            sketch_name,
            plane,
            origin,
            plane_offset,
            profiles,
            angle,
            axis,
            direction,
            operations,
            rotation,
        ) = shape.data
        sweep = pv(angle)
        if not isfinite(sweep) or sweep <= 0 or sweep > 360:
            raise ModelError(
                "sketch revolve angle must be above 0 and at most 360 degrees"
            )
        sketch, meta = compile_standalone_sketch(
            sketch_name,
            plane,
            origin,
            plane_offset,
            profiles,
            operations,
            rotation,
        )
        if isinstance(axis, str):
            native_axis = axis
        else:
            axis_origin, axis_direction = axis
            native_axis = {
                "origin": [
                    command_value(coordinate)
                    for coordinate in axis_origin
                ],
                "dir": list(axis_direction),
            }
        revolve = {
            "sketch": sketch_name,
            "axis": native_axis,
            "angle": command_value(angle),
        }
        if direction is not None:
            revolve["direction"] = direction
        if operation == "new":
            revolve["body_name"] = name
        else:
            revolve["operation"] = operation
            revolve["targets"] = [name]
        sketch.append(_command("solid.revolve", **revolve))
        meta["revolve_axis"] = axis
        return sketch, meta

    if shape.kind == "tapered_box":
        # A straight front mask and a long, smoothly tapered rear housing.
        # from_z is always measured from the Box bottom face, while the Box
        # anchor decides where that bottom face lies in model coordinates.
        original, start, inset = shape.data
        width, height, depth, box_anchor = original.data
        _require_positive(width, "taper width")
        _require_positive(height, "taper height")
        _require_positive(depth, "taper depth")
        if not 0 < pv(start) < pv(depth):
            raise ModelError("taper start lies outside the box")
        if not 0 < 2 * pv(inset) < min(pv(width), pv(height)):
            raise ModelError("taper inset is too large")

        x0, y0, z0 = _box_corner_from_anchor(
            width,
            height,
            depth,
            (0, 0, 0),
            box_anchor,
        )
        x1 = _combine_dimension(x0, width)
        y1 = _combine_dimension(y0, height)
        z_start = _combine_dimension(z0, start)
        z_end = _combine_dimension(z0, depth)

        def shifted(edge, inward):
            # Expression.__str__ is a debug representation that includes
            # fields such as value=... and is not a SolidCraft expression.
            # Convert both operands to typed native values before formatting.
            native_edge = command_value(edge)
            native_offset = command_value(inset)
            if (
                isinstance(native_edge, _NativeExpression)
                or isinstance(native_offset, _NativeExpression)
            ):
                return _native_expression(
                    f"({native_edge}) {'+' if inward else '-'} ({native_offset})",
                    tuple(sorted(_native_dependencies((native_edge, native_offset)))),
                )
            return (native_edge + native_offset if inward
                    else native_edge - native_offset)

        front = f"{name} footprint"
        rear_start = f"{name} rear start"
        rear_end = f"{name} rear perimeter"

        def sketch_rectangle(sketch_name, offset, a, b):
            plane = dict(plane="XY", name=sketch_name)
            if offset != 0:
                plane["offset"] = command_value(offset)
            return [
                _command("sketch.create", **plane),
                _command(
                    "sketch.rectangle.two_point",
                    p0=[command_value(value) for value in a],
                    p1=[command_value(value) for value in b],
                ),
                _command("sketch.finish"),
            ]

        steps = sketch_rectangle(front, z0, [x0, y0], [x1, y1])
        steps.append(_command(
            "solid.extrude", distance=command_value(start), body_name=name,
        ))
        steps.extend(sketch_rectangle(
            rear_start, z_start, [x0, y0], [x1, y1],
        ))
        steps.extend(sketch_rectangle(
            rear_end, z_end,
            [shifted(x0, True), shifted(y0, True)],
            [shifted(x1, False), shifted(y1, False)],
        ))
        steps.append(_command(
            "solid.loft",
            sections=[{"sketch": rear_start}, {"sketch": rear_end}],
            operation="join", targets=[name],
        ))
        return steps, {
            "profile": "rectangle", "width": width, "depth": height,
            "thickness": depth,
            "origin": (x0, y0, z0),
        }

    raise ModelError(f"Expected a Box or explicit Sketch extrusion, got {shape.kind}")
