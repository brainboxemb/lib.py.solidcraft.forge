"""Compiler-owned legacy ordered-feature lowering facade."""

from .detect import _is_pure_csg_tree, _is_feature_tree
from .topology import (
    _face_query_command,
    _next_face_query_index,
    _face_boundary_edge_commands,
    _face_name_commands,
    _resolve_profile_edges,
    _resolve_direction_edges,
    _resolve_feature_edges,
    _edge_params,
    _fillet_command,
    _chamfer_command,
    _shell_command,
)
from .features import (
    _hole_commands,
    _vector,
    _plastic_feature_command,
    _attached_hole_commands,
    _attached_commands,
)
from .sketch import _explicit_sketch_commands
from .parameters import (
    _pattern_count_parameter_names,
    _non_count_parameter_names,
    _pattern_angle_parameter_names,
    _sheet_dimensionless_parameter_names,
)
from .history import (
    _applied_feature_prefix,
    _native_feature_name,
    _named_feature_parent,
    _named_feature_commands,
)
from .dispatch import _to_commands, compile_features

__all__ = ["compile_features"]
