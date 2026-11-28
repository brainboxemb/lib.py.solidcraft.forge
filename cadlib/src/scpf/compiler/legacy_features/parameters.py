"""Legacy pattern and sheet parameter-unit bookkeeping."""

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


def _pattern_count_parameter_names(node, found=None):
    """Collect direct Parameters used as native dimensionless pattern counts."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "rectangular_pattern":
            (
                original, _sources,
                _dir1, count1, _spacing1,
                _dir2, count2, _spacing2,
                _alignment, _alignment2,
                _reversed1, _reversed2,
            ) = node.data
            found.update(param.name for param in parameters_in(count1, count2))
            _pattern_count_parameter_names(original, found)
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, _axis, count, _angle,
                _alignment, _reversed,
            ) = node.data
            found.update(param.name for param in parameters_in(count))
            _pattern_count_parameter_names(original, found)
            return found
        if node.kind == "sketch_pattern_rectangular":
            (
                source, count1, _spacing1, _dir1,
                count2, _spacing2, _dir2,
                _alignment, _alignment2,
                _reversed1, _reversed2,
            ) = node.data
            found.update(param.name for param in parameters_in(count1, count2))
            _pattern_count_parameter_names(source, found)
            return found
        _pattern_count_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _pattern_count_parameter_names(item, found)
    return found


def _non_count_parameter_names(node, found=None):
    """Collect parameter uses outside rectangular-pattern count fields."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "hole":
            spec = _hole_spec(node)
            for field in (
                "diameter",
                "depth",
                "direction",
                "counterbore_diameter",
                "counterbore_depth",
                "countersink_diameter",
                "thread_depth",
                "ease_out",
            ):
                candidate = spec[field]
                if candidate is Depth.THROUGH_ALL or isinstance(candidate, str):
                    continue
                _non_count_parameter_names(candidate, found)
            return found
        if node.kind == "rectangular_pattern":
            (
                original, _sources,
                dir1, _count1, spacing1,
                dir2, _count2, spacing2,
                alignment, alignment2,
                reversed1, reversed2,
            ) = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (dir1, spacing1, dir2, spacing2,
                 alignment, alignment2, reversed1, reversed2),
                found,
            )
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, axis, _count, _angle,
                alignment, reversed,
            ) = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((axis, alignment, reversed), found)
            return found
        if node.kind == "sketch_base_revolve":
            (
                sketch_name,
                plane,
                origin,
                plane_offset,
                profiles,
                _angle,
                axis,
                direction,
                operations,
                rotation,
            ) = node.data
            _non_count_parameter_names(
                (
                    sketch_name,
                    plane,
                    origin,
                    plane_offset,
                    profiles,
                    axis,
                    direction,
                    operations,
                    rotation,
                ),
                found,
            )
            return found
        if node.kind == "sheet_base":
            (
                sketch_name,
                plane,
                origin,
                plane_offset,
                profiles,
                operations,
                thickness,
                bend_radius,
                _k_factor,
                rule_name,
            ) = node.data
            _non_count_parameter_names(
                (
                    sketch_name,
                    plane,
                    origin,
                    plane_offset,
                    profiles,
                    operations,
                    thickness,
                    bend_radius,
                    rule_name,
                ),
                found,
            )
            return found
        if node.kind == "sheet_contour_flange":
            (
                contour,
                distance,
                thickness,
                bend_radius,
                _k_factor,
                rule_name,
                flip,
                reverse,
            ) = node.data
            _non_count_parameter_names(
                (
                    contour,
                    distance,
                    thickness,
                    bend_radius,
                    rule_name,
                    flip,
                    reverse,
                ),
                found,
            )
            return found
        if node.kind == "sheet_edge_flange":
            original, edges, height, _angle, height_from, position, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (edges, height, height_from, position, flip),
                found,
            )
            return found
        if node.kind == "sheet_hem":
            original, edges, length, gap, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((edges, length, gap, flip), found)
            return found
        if node.kind == "sheet_path_flange":
            original, edge, path, radius = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((edge, path, radius), found)
            return found
        if node.kind == "sheet_perforate":
            original, diameter, pitch, margin, pattern = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (diameter, pitch, margin, pattern),
                found,
            )
            return found
        if node.kind == "sheet_fold":
            original, line, _angle, fixed, position, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((line, fixed, position, flip), found)
            return found
        if node.kind == "solid_transform":
            original, translate, _axis, _angle, origin = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((translate, origin), found)
            return found
        if node.kind == "sketch_pattern_rectangular":
            (
                source, _count1, spacing1, dir1,
                _count2, spacing2, dir2,
                alignment, alignment2,
                reversed1, reversed2,
            ) = node.data
            _non_count_parameter_names(source, found)
            _non_count_parameter_names(
                (dir1, spacing1, dir2, spacing2,
                 alignment, alignment2, reversed1, reversed2),
                found,
            )
            return found
        _non_count_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _non_count_parameter_names(item, found)
    else:
        found.update(param.name for param in parameters_in(node))
    return found


def _pattern_angle_parameter_names(node, found=None):
    """Collect direct Parameters used as native angle fields in degrees."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "hole":
            angle = _hole_spec(node)["countersink_angle"]
            if angle is not None:
                found.update(param.name for param in parameters_in(angle))
            return found
        if node.kind == "sketch_base_revolve":
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
            ) = node.data
            found.update(param.name for param in parameters_in(angle))
            return found
        if node.kind == "sheet_edge_flange":
            original, _edges, _height, angle, _height_from, _position, _flip = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        if node.kind == "sheet_fold":
            original, _line, angle, _fixed, _position, _flip = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, _axis, _count, angle,
                _alignment, _reversed,
            ) = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        if node.kind == "solid_transform":
            original, _translate, _axis, angle, _origin = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        _pattern_angle_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _pattern_angle_parameter_names(item, found)
    return found


def _sheet_dimensionless_parameter_names(node, found=None):
    """Collect direct Parameters used as dimensionless sheet-rule values."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "sheet_base":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                _operations,
                _thickness,
                _bend_radius,
                k_factor,
                _rule_name,
            ) = node.data
            found.update(param.name for param in parameters_in(k_factor))
            return found
        if node.kind == "sheet_contour_flange":
            (
                _contour,
                _distance,
                _thickness,
                _bend_radius,
                k_factor,
                _rule_name,
                _flip,
                _reverse,
            ) = node.data
            found.update(param.name for param in parameters_in(k_factor))
            return found
        _sheet_dimensionless_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _sheet_dimensionless_parameter_names(item, found)
    return found


_AUTO_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.hole": "Hole",
}
