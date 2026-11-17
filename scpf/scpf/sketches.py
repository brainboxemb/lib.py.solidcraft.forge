"""Native SolidCraft sketch construction for primitive CAD profiles.

Each supported base shape returns its command list plus simple shape metadata.
Feature operations (Hole, Fillet, join, cut) are handled separately.
"""
from math import isfinite
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

def compile_base(shape, name):
    """Create a native editable base body, regardless of example/model name."""
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
        if len(shape.data) == 8:
            (
                sketch_name,
                plane,
                origin,
                plane_offset,
                profiles,
                distance,
                direction,
                operations,
            ) = shape.data
            if operations:
                raise ModelError(
                    "sketch pattern/mirror currently requires an attached Sketch"
                )
        else:
            sketch_name, plane, origin, plane_offset, profiles, distance, direction = shape.data
        _require_positive(distance, "sketch extrusion distance")
        if plane not in ("XY", "XZ", "YZ"):
            raise ModelError("standalone Sketch requires an XY, XZ or YZ plane")
        if len(profiles) != 1:
            raise ModelError("standalone Sketch currently requires exactly one profile")
        profile, profile_anchor, (ox, oy) = profiles[0]
        if origin is not None:
            raise ModelError("standalone Sketch origin is not supported yet")
        sketch_params = {"plane": plane, "name": sketch_name}
        if plane_offset is not None:
            sketch_params["offset"] = command_value(plane_offset)
        sketch = [_command("sketch.create", **sketch_params)]
        if profile.kind == "rectangle":
            width, depth = profile.data
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
            sketch.append(_command(
                "sketch.rectangle.two_point",
                p0=[command_value(x0), command_value(y0)],
                p1=[command_value(x1), command_value(y1)],
            ))
            meta = {
                "profile": "rectangle",
                "width": width,
                "depth": depth,
                "thickness": distance,
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
            meta = {"profile": "circle", "thickness": distance}
        elif profile.kind == "polygon":
            if profile_anchor is not None:
                raise ModelError(
                    "Polygon2D uses authored sketch coordinates; "
                    "semantic CENTER is not supported yet"
                )
            points, profile_plane, ids = profile.data
            if profile_plane != plane:
                raise ModelError("Polygon2D plane must match Sketch plane")
            if pv(ox) or pv(oy):
                raise ModelError("standalone Polygon2D offset is not supported yet")
            concrete = [tuple(pv(v) for v in point) for point in points]
            if not all(isfinite(v) for point in concrete for v in point):
                raise ModelError("non-finite polygon coordinate")
            if len(set(concrete)) != len(concrete):
                raise ModelError("duplicate polygon vertices")
            if any(a == b for a, b in zip(concrete, concrete[1:] + concrete[:1])):
                raise ModelError("zero-length polygon edge")
            sketch.append(_command("sketch.line",
                points=[[command_value(v) for v in point] for point in points],
                closed=True, ids=list(ids) if ids is not None else
                [chr(ord("a") + i) for i in range(len(points))]))
            meta = {"profile": "polygon", "sketch_plane": plane,
                    "sketch_plane_offset": plane_offset if plane_offset is not None else 0,
                    "thickness": distance,
                    "extrusion_direction": direction,
                    "profile_points": points, "profile_ids": ids}
        else:
            raise ModelError("standalone Sketch supports Rectangle2D, Circle2D and Polygon2D")
        sketch.extend([_command("sketch.finish"),
            _command("solid.extrude", distance=command_value(distance),
                     direction=direction, body_name=name)])
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
