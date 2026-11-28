"""Mitcad backend facade; lowering is owned by semantic-domain modules."""
from .common import (
    _parameter_commands,
    _role_scalar_expression_text,
    _role_command_value,
)
from .sketch import (
    _principal_plane_offset,
    _mitcad_offset_plane,
    _mitcad_sketch_plane,
    _same_semantic_value,
    _sketch_relations_transport,
    _next_sketch_entity_number,
    _next_sketch_relation_number,
    _shifted_xy_axis_transport,
    _mitcad_revolve_axis,
)
from .primitives import (
    _require_origin_plane,
    _box_command,
    _cylinder_plane_center,
    _cylinder_command,
    _cone_commands,
    _sphere_center,
    _sphere_command,
    _sphere_commands,
    _csg_helper_binding,
    _csg_primitive_commands,
)
from .operations import (
    _boolean_command_plan,
    _boolean_commands,
    _boolean_feature_command_index,
    _extrude_commands,
    _revolve_commands,
    _revolve_cut_document,
    _fillet_document,
    _chamfer_document,
    _translated_body_ir,
    _materialize_translations,
    _contains_translation,
)
from .configuration import (
    _private_suppression_parameter,
    _mitcad_configuration_commands,
    _qualified_configuration_slice,
)
from .dispatch import (
    compile_ir_with_dependencies,
    compile_ir,
    compile_model_with_dependencies,
    compile_model,
)

__all__ = ["compile_ir", "compile_ir_with_dependencies", "compile_model", "compile_model_with_dependencies"]
