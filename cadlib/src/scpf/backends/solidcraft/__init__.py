"""SolidCraft backend facade; lowering is owned by semantic-domain modules."""
from .common import (
    _require_positive,
    _command,
    _parameter_commands,
    _role_scalar_expression_text,
    _role_command_value,
    _negative_half,
    _negative_value,
)
from .primitives import (
    _origin_box_corner,
    _box_command,
    _cylinder_command,
    _cone_command,
    _sphere_command,
    _csg_primitive_command,
)
from .sketch import (
    _principal_plane_offset,
    _solidcraft_sketch_create,
    _typed_rectangular_support,
    _solidcraft_sketch_support_commands,
    _next_sketch_index,
    _solidcraft_relation_polygon_points,
    _solidcraft_dimension_sum,
    _solidcraft_profile_commands,
    _solidcraft_axis,
    _sketch_chain_geometry_commands,
    _solidcraft_sketch_graph_commands,
)
from .features import (
    _parallel_box_edge_picks,
    _typed_rectangular_base,
    _typed_shell_thickness,
    _feature_offset_value,
    _anchored_feature_position,
    _absolute_hole_command,
    _anchored_hole_commands,
    _hole_commands,
    _plastic_feature_command_ir,
    _plastic_feature_commands,
    _typed_feature_name,
    _rectangular_pattern_commands,
    _circular_pattern_commands,
)
from .operations import (
    _fillet_commands,
    _translated_body_ir,
    _csg_style_tool,
    _boolean_tool_commands,
    _boolean_commands,
    _extrude_commands,
    _revolve_commands,
    _next_face_query_index,
    _face_query_command,
    _face_boundary_commands,
    _rectangular_edge_picks,
    _profile_source_extrude,
    _profile_edge_picks,
    _edge_selection_commands,
    _face_name_commands,
    _chamfer_commands,
    _shell_commands,
)
from .sheet_metal import (
    _sheet_rule_command,
    _sheet_chain_commands,
    _sheet_base_commands,
    _sheet_contour_commands,
    _sheet_fold_commands,
    _sheet_edge_flange_commands,
    _sheet_hem_commands,
    _sheet_path_flange_commands,
    _sheet_perforate_commands,
)
from .configuration import (
    _boolean_command_count,
    _boolean_feature_command_index,
    _history_command_indexes,
    _semantic_feature_command_index,
    _configured_feature_command_index,
    _portable_named_feature_commands,
    _portable_configuration_commands,
)
from .dispatch import (
    _body_commands,
    _portable_commands,
    compile_ir_commands_with_dependencies,
    compile_ir_with_dependencies,
    compile_ir,
)

__all__ = ["compile_ir", "compile_ir_with_dependencies", "compile_ir_commands_with_dependencies"]
