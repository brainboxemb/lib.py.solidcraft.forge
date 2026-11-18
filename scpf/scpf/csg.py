"""CSG primitive translation to native SolidCraft commands.

This module is not a geometry engine. SolidCraft executes these operations.
"""
from .core import (
    Shape,
    Parameter,
    Expression,
    _NativeExpression,
    _native_expression,
    _box_corner_from_anchor,
    _sphere_center_from_anchor,
    _cylinder_base_from_anchor,
    _cone_base_from_anchor,
    _pv as pv,
    command_value,
    number_text,
)
from .compiler import ModelError, _command, _require_positive


CSG_PRIMITIVE_KINDS = frozenset(("box", "sphere", "cylinder", "cone"))


def _half(dim, negative=False):
    if isinstance(dim, Parameter):
        return _native_expression(
            f"-{dim.name} / 2" if negative else f"{dim.name} / 2",
            (dim.name,),
        )
    if isinstance(dim, Expression):
        expression = command_value(dim)
        return _native_expression(
            f"-({expression}) / 2"
            if negative
            else f"({expression}) / 2",
            expression.parameters,
        )
    return -pv(dim) / 2 if negative else pv(dim) / 2


def _shift(offset, delta):
    """Combine CSG offsets without polluting symbolic expressions with + 0."""
    result = []
    for current, added in zip(offset, delta):
        if current == 0:
            result.append(added)
        elif added == 0:
            result.append(current)
        else:
            result.append(current + added)
    return tuple(result)


def _add_offset(coord, offset):
    """Offset either a literal coordinate or a SolidCraft expression."""
    if not offset:
        return coord
    if isinstance(coord, _NativeExpression):
        return _native_expression(
            f"({coord}) + {number_text(offset)}",
            coord.parameters,
        )
    return coord + offset


def _csg_primitive(shape, body_name, operation, *, offset=(0, 0, 0)):
    kind, data = shape.kind, shape.data
    if kind == "box":
        length, width, height, anchor = data
        _require_positive(length, "box length")
        _require_positive(width, "box width")
        _require_positive(height, "box height")
        params = dict(
            length=command_value(length),
            width=command_value(width),
            height=command_value(height),
            operation=operation,
        )
        if anchor.vector == (0, 0, 0):
            params["center"] = [
                command_value(value) for value in offset
            ]
        else:
            corner = _box_corner_from_anchor(
                length,
                width,
                height,
                offset,
                anchor,
            )
            params["corner"] = [
                command_value(value) for value in corner
            ]
        command = "solid.box"
    elif kind == "sphere":
        radius, anchor = data
        _require_positive(radius, "sphere radius")
        center = _sphere_center_from_anchor(radius, offset, anchor)
        params = dict(
            radius=command_value(radius),
            center=[command_value(value) for value in center],
            operation=operation,
        )
        command = "solid.sphere"
    elif kind == "cylinder":
        height, diameter, axis, anchor = data
        _require_positive(height, "cylinder height")
        _require_positive(diameter, "cylinder diameter")
        base = _cylinder_base_from_anchor(height, diameter, axis, offset, anchor)
        params = dict(height=command_value(height),
                      diameter=command_value(diameter),
                      base=[command_value(value) for value in base],
                      axis=axis, operation=operation)
        command = "solid.cylinder"
    elif kind == "cone":
        height, diameter, top_diameter, axis, anchor = data
        _require_positive(height, "cone height")
        _require_positive(diameter, "cone diameter")
        top_value = pv(top_diameter)
        if top_value < 0:
            raise ModelError("cone top diameter must be zero or positive")
        base = _cone_base_from_anchor(height, axis, offset, anchor)
        params = dict(
            height=command_value(height),
            diameter=command_value(diameter),
            top_diameter=command_value(top_diameter),
            base=[command_value(value) for value in base],
            axis=axis,
            operation=operation,
        )
        command = "solid.cone"
    else:
        raise ModelError(f"not a supported CSG primitive: {kind}")

    if operation == "new":
        params["body_name"] = body_name
    else:
        params["targets"] = [body_name]
    return _command(command, **params)


def _csg_apply(shape, name, operation, offset=(0, 0, 0)):
    if shape.kind == "placed_box":
        box, x, y, z, anchor = shape.data
        length, width, height, _ = box.data
        placed = Shape("box", (length, width, height, anchor))
        return _csg_apply(
            placed,
            name,
            operation,
            (command_value(x), command_value(y), command_value(z)),
        )
    if shape.kind == "placed3d":
        child, x, y, z = shape.data
        if child.kind not in ("cylinder", "cone"):
            raise ModelError("Only Cylinder and Cone support 3D CSG placement")
        return _csg_apply(
            child, name, operation,
            (command_value(x), command_value(y), command_value(z)),
        )
    if shape.kind == "translated":
        child, delta = shape.data
        return _csg_apply(child, name, operation, _shift(offset, delta))
    if shape.kind in CSG_PRIMITIVE_KINDS:
        return [_csg_primitive(shape, name, operation, offset=offset)]
    if shape.kind == "union" and operation in ("cut", "join"):
        left, right = shape.data
        return _csg_apply(left, name, operation, offset) + _csg_apply(right, name, operation, offset)
    raise ModelError(f"unsupported CSG {operation}: {shape.kind}")


def _csg_new(shape, name, offset=(0, 0, 0)):
    if shape.kind == "placed_box":
        box, x, y, z, anchor = shape.data
        length, width, height, _ = box.data
        placed = Shape("box", (length, width, height, anchor))
        return _csg_new(
            placed,
            name,
            (command_value(x), command_value(y), command_value(z)),
        )
    if shape.kind == "placed3d":
        child, x, y, z = shape.data
        if child.kind not in ("cylinder", "cone"):
            raise ModelError("Only Cylinder and Cone are supported by 3D placement")
        return _csg_new(child, name, (command_value(x), command_value(y), command_value(z)))
    if shape.kind == "translated":
        child, delta = shape.data
        return _csg_new(child, name, _shift(offset, delta))
    if shape.kind in CSG_PRIMITIVE_KINDS:
        return [_csg_primitive(shape, name, "new", offset=offset)]
    if shape.kind == "intersection":
        left, right = shape.data
        return _csg_new(left, name, offset) + _csg_apply(right, name, "intersect", offset)
    if shape.kind == "difference":
        left, right = shape.data
        return _csg_new(left, name, offset) + _csg_apply(right, name, "cut", offset)
    if shape.kind == "union":
        left, right = shape.data
        return _csg_new(left, name, offset) + _csg_apply(right, name, "join", offset)
    raise ModelError(f"unsupported root CSG shape: {shape.kind}")


