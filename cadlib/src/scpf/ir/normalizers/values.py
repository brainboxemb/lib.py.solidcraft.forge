"""Parameter and semantic value normalization.

Private normalization module behind :mod:`scpf.ir`.
"""
from __future__ import annotations

from ...core import Depth, Parameter, Shape, _hole_spec, parameters_in
from ..base import ParameterIR
from ..body import LegacyShapeIR

def _collect_parameters(value, found=None):
    """Collect named symbolic parameters in deterministic first-use order."""
    if found is None:
        found = {}

    if isinstance(value, Shape):
        _collect_parameters(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _collect_parameters(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _collect_parameters(item, found)
        return found

    for parameter in parameters_in(value):
        previous = found.setdefault(parameter.name, parameter.value)
        if previous != parameter.value:
            raise ValueError(
                f"conflicting values for parameter {parameter.name}"
            )
    return found


def _count_parameter_names(value, found=None):
    """Collect direct Parameters used as unitless native feature counts."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "rectangular_pattern":
            (
                original,
                _sources,
                _dir1,
                count1,
                _spacing1,
                _dir2,
                count2,
                _spacing2,
                _alignment1,
                _alignment2,
                _reversed1,
                _reversed2,
            ) = value.data
            found.update(
                parameter.name
                for parameter in parameters_in(count1, count2)
            )
            _count_parameter_names(original, found)
            return found
        if value.kind == "sketch_pattern_rectangular":
            (
                source,
                count,
                _spacing,
                _direction,
                count2,
                _spacing2,
                _direction2,
                _alignment,
                _alignment2,
                _reversed,
                _reversed2,
            ) = value.data
            found.update(
                parameter.name
                for parameter in parameters_in(count, count2)
            )
            _count_parameter_names(source, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                _axis,
                count,
                _angle,
                _alignment,
                _reversed,
            ) = value.data
            found.update(
                parameter.name for parameter in parameters_in(count)
            )
            _count_parameter_names(original, found)
            return found
        _count_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _count_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _count_parameter_names(item, found)
    return found


def _angle_parameter_names(value, found=None):
    """Collect parameters whose qualified semantic role is an angle."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "hole":
            angle = _hole_spec(value)["countersink_angle"]
            if angle is not None:
                found.update(
                    parameter.name for parameter in parameters_in(angle)
                )
            return found
        if value.kind == "sheet_fold":
            original, _line, angle, _fixed, _position, _flip = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
            _angle_parameter_names(original, found)
            return found
        if value.kind == "sheet_edge_flange":
            original, _edges, _height, angle, _height_from, _position, _flip = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
            _angle_parameter_names(original, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                _axis,
                _count,
                angle,
                _alignment,
                _reversed,
            ) = value.data
            if angle is not None:
                found.update(
                    parameter.name for parameter in parameters_in(angle)
                )
            _angle_parameter_names(original, found)
            return found
        if value.kind == "sketch_base_revolve":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                angle,
                _axis,
                _direction,
                _operations,
                _rotation,
            ) = value.data
            found.update(parameter.name for parameter in parameters_in(angle))
        _angle_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _angle_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _angle_parameter_names(item, found)
    return found


def _length_parameter_names(value, found=None):
    """Collect parameters used in the currently-qualified length-valued slots."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "hole":
            spec = _hole_spec(value)
            for field in (
                "diameter",
                "depth",
                "counterbore_diameter",
                "counterbore_depth",
                "countersink_diameter",
                "thread_depth",
            ):
                candidate = spec[field]
                if candidate is not None and candidate is not Depth.THROUGH_ALL:
                    _length_parameter_names(candidate, found)
            ease_out = spec["ease_out"]
            if ease_out is not None and not isinstance(ease_out, str):
                _length_parameter_names(ease_out, found)
            # Parameter-driven direction is outside typed Hole semantics in
            # #550. Retain its compatibility role while such a model remains
            # on LegacyShapeIR instead of misclassifying countersink angle.
            direction = spec["direction"]
            if direction is not None:
                _length_parameter_names(direction, found)
            return found
        if value.kind == "sheet_base":
            (
                _sketch_name, _plane, origin, plane_offset, profiles, operations,
                thickness, bend_radius, _k_factor, _rule_name,
            ) = value.data
            _length_parameter_names(
                (origin, plane_offset, profiles, operations, thickness, bend_radius),
                found,
            )
            return found
        if value.kind == "sheet_contour_flange":
            contour, distance, thickness, bend_radius, _k_factor, _rule_name, _flip, _reverse = value.data
            _length_parameter_names(
                (contour, distance, thickness, bend_radius),
                found,
            )
            return found
        if value.kind == "sheet_fold":
            original, line, _angle, fixed, _position, _flip = value.data
            _length_parameter_names((original, line, fixed), found)
            return found
        if value.kind == "sheet_edge_flange":
            original, _edges, height, _angle, _height_from, _position, _flip = value.data
            _length_parameter_names((original, height), found)
            return found
        if value.kind == "sheet_hem":
            original, _edges, length, gap, _flip = value.data
            _length_parameter_names((original, length, gap), found)
            return found
        if value.kind == "sheet_path_flange":
            original, _edge, path, radius = value.data
            _length_parameter_names((original, path, radius), found)
            return found
        if value.kind == "sheet_perforate":
            original, diameter, pitch, margin, _pattern = value.data
            _length_parameter_names((original, diameter, pitch, margin), found)
            return found
        if value.kind == "rectangular_pattern":
            (
                original,
                _sources,
                _dir1,
                _count1,
                spacing1,
                _dir2,
                _count2,
                spacing2,
                _alignment1,
                _alignment2,
                _reversed1,
                _reversed2,
            ) = value.data
            _length_parameter_names(original, found)
            _length_parameter_names(spacing1, found)
            if spacing2 is not None:
                _length_parameter_names(spacing2, found)
            return found
        if value.kind == "sketch_pattern_rectangular":
            (
                source,
                _count,
                spacing,
                _direction,
                _count2,
                spacing2,
                _direction2,
                _alignment,
                _alignment2,
                _reversed,
                _reversed2,
            ) = value.data
            _length_parameter_names(source, found)
            _length_parameter_names(spacing, found)
            if spacing2 is not None:
                _length_parameter_names(spacing2, found)
            return found
        if value.kind == "circular_pattern":
            (
                original,
                _sources,
                axis,
                _count,
                _angle,
                _alignment,
                _reversed,
            ) = value.data
            _length_parameter_names(original, found)
            if not isinstance(axis, str):
                origin, _direction = axis
                _length_parameter_names(origin, found)
            return found
        if value.kind == "sketch_base_revolve":
            # The Revolve sweep is the only currently-qualified angle-valued
            # Shape payload. Every other symbolic value in this payload retains
            # the pre-existing CAD-length interpretation.
            for index, item in enumerate(value.data):
                if index != 5:
                    _length_parameter_names(item, found)
            return found
        _length_parameter_names(value.data, found)
        return found

    if isinstance(value, dict):
        for item in value.values():
            _length_parameter_names(item, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _length_parameter_names(item, found)
        return found

    found.update(parameter.name for parameter in parameters_in(value))
    return found


def _ratio_parameter_names(value, found=None):
    """Collect dimensionless continuous sheet-rule parameters."""
    if found is None:
        found = set()

    if isinstance(value, Shape):
        if value.kind == "sheet_base":
            _sketch_name, _plane, _origin, _offset, _profiles, _operations, _thickness, _radius, k_factor, _rule = value.data
            found.update(parameter.name for parameter in parameters_in(k_factor))
            return found
        if value.kind == "sheet_contour_flange":
            contour, _distance, _thickness, _radius, k_factor, _rule, _flip, _reverse = value.data
            found.update(parameter.name for parameter in parameters_in(k_factor))
            _ratio_parameter_names(contour, found)
            return found
        _ratio_parameter_names(value.data, found)
        return found

    if isinstance(value, (tuple, list)):
        for item in value:
            _ratio_parameter_names(item, found)
    return found


def _parameter_ir(shape: Shape) -> tuple[ParameterIR, ...]:
    values = _collect_parameters(shape)
    length_parameters = _length_parameter_names(shape)
    angle_parameters = _angle_parameter_names(shape)
    count_parameters = _count_parameter_names(shape)
    ratio_parameters = _ratio_parameter_names(shape)
    return tuple(
        ParameterIR(
            name,
            value,
            roles=tuple(
                role
                for role, names in (
                    ("length", length_parameters),
                    ("angle", angle_parameters),
                    ("count", count_parameters),
                    ("ratio", ratio_parameters),
                )
                if name in names
            ),
        )
        for name, value in values.items()
    )
