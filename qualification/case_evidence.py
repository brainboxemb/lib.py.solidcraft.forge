"""Case-specific Q1/Q2 test evidence for qualification.

Q1 targets live in scpf/tests and prove public Python API, validation or
compiler behaviour. Q2 targets live beside the qualification example under
examples/<case>/tests and assert the command contract of that fixture.
"""

from pathlib import Path

from qualification.cases import supported_qualification_cases


ROOT = Path(__file__).resolve().parents[1]


def _target(file: str, test: str) -> dict[str, str]:
    return {"file": file, "test": test}


CASE_EVIDENCE = {
    "simple-box": {
        "q1": [
            _target(
                "scpf/tests/test_model_authoring.py",
                "test_plain_model_class_fields_become_parameters",
            ),
        ],
        "q2": [
            _target(
                "examples/simple-box/tests/test_contract.py",
                "test_box_lowers_directly_to_native_solid_box",
            ),
        ],
    },
    "anchored-holes": {
        "q1": [
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_repeat_linear_is_not_part_of_the_public_shape_api",
            ),
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_attached_hole_source_uses_native_rectangular_pattern",
            ),
        ],
        "q2": [
            _target(
                "examples/anchored-holes/tests/test_contract.py",
                "test_anchored_holes_command_contract",
            ),
        ],
    },
    "hole-family": {
        "q1": [
            _target(
                "scpf/tests/test_hole_family.py",
                "test_all_hole_variants_lower_one_to_one_to_native_hole",
            ),
            _target(
                "scpf/tests/test_hole_family.py",
                "test_hole_family_validates_feature_specific_dimensions",
            ),
            _target(
                "scpf/tests/test_hole_family.py",
                "test_threaded_hole_keeps_cosmetic_and_modeled_intent_distinct",
            ),
        ],
        "q2": [
            _target(
                "examples/hole-family/tests/test_contract.py",
                "test_hole_family_uses_four_native_hole_features",
            ),
        ],
    },
    "sheet-fold": {
        "q1": [
            _target(
                "scpf/tests/test_sheet_metal.py",
                "test_blank_hole_and_fold_lower_to_native_sheet_history",
            ),
            _target(
                "scpf/tests/test_sheet_metal.py",
                "test_sheet_rule_and_fold_parameter_units_are_correct",
            ),
            _target(
                "scpf/tests/test_sheet_metal.py",
                "test_sheet_metal_and_fold_validate_authoring_contract",
            ),
        ],
        "q2": [
            _target(
                "examples/sheet-fold/tests/test_contract.py",
                "test_sheet_fold_uses_native_sheet_history",
            ),
            _target(
                "examples/sheet-fold/tests/test_contract.py",
                "test_sheet_rule_and_fold_parameters_have_native_units",
            ),
        ],
    },
    "top-sketch-after-chamfer": {
        "q1": [
            _target(
                "scpf/tests/test_headless.py",
                "test_numeric_vector_selector_tolerates_kernel_float_noise",
            ),
            _target(
                "scpf/tests/test_sketch_attachment.py",
                "test_top_attached_sketch_uses_same_face_query_after_edge_features",
            ),
        ],
        "q2": [
            _target(
                "examples/top-sketch-after-chamfer/tests/test_contract.py",
                "test_chamfer_precedes_native_face_query_and_attached_sketch",
            ),
        ],
    },
    "parameter-scope": {
        "q1": [
            _target(
                "scpf/tests/test_component_definitions.py",
                "test_component_defaults_are_fixed_unless_included",
            ),
        ],
        "q2": [
            _target(
                "examples/parameter-scope/tests/test_contract.py",
                "test_generated_parameter_contract",
            ),
        ],
    },
    "parent-derived-child-size": {
        "q1": [
            _target(
                "scpf/tests/test_component_definitions.py",
                "test_parent_expression_remains_an_expression_in_child_geometry",
            ),
        ],
        "q2": [
            _target(
                "examples/parent-derived-child-size/tests/test_contract.py",
                "test_child_dimensions_keep_parent_expressions",
            ),
        ],
    },
    "components": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_placement.py",
                "test_copy_accepts_placement_override",
            ),
        ],
        "q2": [
            _target(
                "examples/components/tests/test_contract.py",
                "test_components_command_contract",
            ),
        ],
    },
    "repeated-parent-attachments": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_repeated_parent_attachments_keep_distinct_targets",
            ),
        ],
        "q2": [
            _target(
                "examples/repeated-parent-attachments/tests/test_contract.py",
                "test_two_authored_rigid_joints_use_bound_occurrences",
            ),
        ],
    },
    "assembly-decorator": {
        "q1": [
            _target(
                "scpf/tests/test_component_definitions.py",
                "test_imported_assembly_class_uses_object_syntax",
            ),
        ],
        "q2": [
            _target(
                "examples/assembly-decorator/tests/test_contract.py",
                "test_imported_assembly_lowers_to_reusable_native_occurrences",
            ),
        ],
    },
    "group-hierarchy": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_placement.py",
                "test_named_group_creates_real_nested_native_component",
            ),
        ],
        "q2": [
            _target(
                "examples/group-hierarchy/tests/test_contract.py",
                "test_group_lowers_to_real_nested_component",
            ),
        ],
    },
    "attach-angle": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_attach_angle_is_emitted_as_native_joint_turn",
            ),
        ],
        "q2": [
            _target(
                "examples/attach-angle/tests/test_contract.py",
                "test_quarter_turn_is_emitted_on_rigid_joint",
            ),
        ],
    },
    "parametric-attach": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_parametric_attach_keeps_gap_as_native_joint_expression",
            ),
        ],
        "q2": [
            _target(
                "examples/parametric-attach/tests/test_contract.py",
                "test_parametric_attach_command_contract",
            ),
        ],
    },
    "parametric-offset": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_parametric_attach_keeps_in_plane_offset_expression",
            ),
        ],
        "q2": [
            _target(
                "examples/parametric-offset/tests/test_contract.py",
                "test_parametric_offset_command_contract",
            ),
        ],
    },
    "parametric-anchor": {
        "q1": [
            _target(
                "scpf/tests/test_component_definitions.py",
                "test_component_preserves_parent_parameter_dependency",
            ),
        ],
        "q2": [
            _target(
                "examples/parametric-anchor/tests/test_contract.py",
                "test_parametric_anchor_command_contract",
            ),
        ],
    },
    "corner-anchor": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_corner_anchor_compiles_to_native_edge_and_corner_origins",
            ),
        ],
        "q2": [
            _target(
                "examples/corner-anchor/tests/test_contract.py",
                "test_corner_anchor_command_contract",
            ),
        ],
    },
    "anchor-topology-mutation": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_named_topology_anchor_is_inlined_as_edge_reference",
            ),
        ],
        "q2": [
            _target(
                "examples/anchor-topology-mutation/tests/test_contract.py",
                "test_fixed_topology_pick_is_inlined",
            ),
        ],
    },
    "assembly-owned-anchor": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_attachments.py",
                "test_assembly_can_own_named_attachment_anchor",
            ),
        ],
        "q2": [
            _target(
                "examples/assembly-owned-anchor/tests/test_contract.py",
                "test_named_assembly_anchor_resolves_to_native_corner_relationship",
            ),
        ],
    },
    "four-corner-l": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_placement.py",
                "test_symbolic_ordinary_copy_placement_keeps_parameter",
            ),
        ],
        "q2": [
            _target(
                "examples/four-corner-l/tests/test_contract.py",
                "test_parametric_profile_placement_uses_replay_variables",
            ),
        ],
    },
    "eight-corner-brackets": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_placement.py",
                "test_symbolic_ordinary_copy_placement_keeps_parameter",
            ),
        ],
        "q2": [
            _target(
                "examples/eight-corner-brackets/tests/test_contract.py",
                "test_parametric_profile_placement_uses_replay_variables",
            ),
        ],
    },
    "eight-flightcase-corners": {
        "q1": [
            _target(
                "scpf/tests/test_assembly_placement.py",
                "test_symbolic_copy_with_rotation_uses_bound_native_move",
            ),
        ],
        "q2": [
            _target(
                "examples/eight-flightcase-corners/tests/test_contract.py",
                "test_parametric_corner_placement_uses_replay_variables",
            ),
        ],
    },
    "xz-anchor": {
        "q1": [
            _target(
                "scpf/tests/test_component_definitions.py",
                "test_xz_rectangular_component_uses_standard_corner_anchor",
            ),
        ],
        "q2": [
            _target(
                "examples/xz-anchor/tests/test_contract.py",
                "test_xz_anchor_command_contract",
            ),
        ],
    },
    "round-top-sketch": {
        "q1": [
            _target(
                "scpf/tests/test_sketch_attachment.py",
                "test_top_attached_sketch_supports_circular_extrusion_body",
            ),
            _target(
                "scpf/tests/test_sketch_attachment.py",
                "test_explicit_plane_origin_sketch_supports_circular_body",
            ),
        ],
        "q2": [
            _target(
                "examples/round-top-sketch/tests/test_contract.py",
                "test_top_face_query_is_used_after_circular_base_extrusion",
            ),
        ],
    },
    "circle-negative-extrude": {
        "q1": [
            _target(
                "scpf/tests/test_sketch_profiles.py",
                "test_circle_in_with_sketch_negative_extrusion",
            ),
        ],
        "q2": [
            _target(
                "examples/circle-negative-extrude/tests/test_contract.py",
                "test_signed_distance_preserves_negative_native_direction",
            ),
        ],
    },
    "sketch-pattern-mirror": {
        "q1": [
            _target(
                "scpf/tests/test_sketch_patterns.py",
                "test_circle_rectangular_pattern_uses_bound_native_curves",
            ),
            _target(
                "scpf/tests/test_sketch_patterns.py",
                "test_slot_pattern_and_mirrors_reuse_operation_results",
            ),
            _target(
                "scpf/tests/test_sketch_patterns.py",
                "test_pattern_count_and_spacing_remain_native_parameters",
            ),
        ],
        "q2": [
            _target(
                "examples/sketch-pattern-mirror/tests/test_contract.py",
                "test_circle_seed_stays_one_native_profile_with_pattern_and_mirror",
            ),
            _target(
                "examples/sketch-pattern-mirror/tests/test_contract.py",
                "test_slot_seed_stays_one_native_profile_with_pattern_and_mirrors",
            ),
            _target(
                "examples/sketch-pattern-mirror/tests/test_contract.py",
                "test_pattern_parameters_have_correct_native_units",
            ),
        ],
    },
    "selective-profile-extrude": {
        "q1": [
            _target(
                "scpf/tests/test_sketch_patterns.py",
                "test_pattern_can_feed_one_selective_profile_extrusion",
            ),
        ],
        "q2": [
            _target(
                "examples/selective-profile-extrude/tests/test_contract.py",
                "test_one_pattern_and_one_selective_native_extrusion",
            ),
            _target(
                "examples/selective-profile-extrude/tests/test_contract.py",
                "test_saved_design_mutation_changes_seed_and_pattern_spacing",
            ),
        ],
    },
    "circular-feature-pattern": {
        "q1": [
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_circular_pattern_emits_one_native_feature_pattern",
            ),
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_circular_pattern_validates_shared_feature_and_axis_options",
            ),
        ],
        "q2": [
            _target(
                "examples/circular-feature-pattern/tests/test_contract.py",
                "test_emits_one_native_circular_feature_pattern",
            ),
            _target(
                "examples/circular-feature-pattern/tests/test_contract.py",
                "test_count_parameter_is_dimensionless_and_pcd_is_length",
            ),
        ],
    },
    "rectangular-pattern": {
        "q1": [
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_rectangular_pattern_requires_applied_extrude_feature",
            ),
        ],
        "q2": [
            _target(
                "examples/rectangular-pattern/tests/test_contract.py",
                "test_emits_one_native_feature_pattern",
            ),
            _target(
                "examples/rectangular-pattern/tests/test_contract.py",
                "test_count_parameters_are_dimensionless",
            ),
        ],
    },
    "slot-family": {
        "q1": [
            _target(
                "scpf/tests/test_native_slots.py",
                "test_all_five_slot_variants_lower_one_to_one",
            ),
            _target(
                "scpf/tests/test_native_slots.py",
                "test_arc_center_requires_one_end_definition",
            ),
        ],
        "q2": [
            _target(
                "examples/slot-family/tests/test_contract.py",
                "test_slot_family_command_contract",
            ),
        ],
    },
    "rounded-rectangle-sketch": {
        "q1": [
            _target(
                "scpf/tests/test_geometry_features.py",
                "test_rounded_rectangle_sketch_compiles_to_true_native_arcs",
            ),
        ],
        "q2": [
            _target(
                "examples/rounded-rectangle-sketch/tests/test_contract.py",
                "test_named_sketch_uses_native_rounded_rectangle",
            ),
        ],
    },
    "primitive-csg": {
        "q1": [
            _target(
                "scpf/tests/test_geometry_primitives.py",
                "test_move_translates_a_csg_composite_without_changing_sizes",
            ),
            _target(
                "scpf/tests/test_geometry_primitives.py",
                "test_cylinder_axis_lowers_directly_to_native_axis",
            ),
        ],
        "q2": [
            _target(
                "examples/primitive-csg/tests/test_contract.py",
                "test_generated_command_contract",
            ),
        ],
    },
    "bracket": {
        "q1": [
            _target(
                "scpf/tests/test_sketch_profiles.py",
                "test_positioned_xz_polygon_keeps_parameterized_y_plane",
            ),
            _target(
                "scpf/tests/test_sketch_extrusion.py",
                "test_sketch_extrude_signed_distance_and_sym",
            ),
        ],
        "q2": [
            _target(
                "examples/bracket/tests/test_contract.py",
                "test_bracket_command_contract",
            ),
        ],
    },
}


def validate_case_evidence() -> None:
    expected = {case["slug"] for case in supported_qualification_cases()}
    actual = set(CASE_EVIDENCE)
    if expected != actual:
        raise ValueError(
            "case evidence mismatch; "
            f"missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )

    for slug, levels in CASE_EVIDENCE.items():
        for level, prefix in (
            ("q1", "scpf/tests/"),
            ("q2", f"examples/{slug}/tests/"),
        ):
            targets = levels.get(level) or []
            if not targets:
                raise ValueError(
                    f"{slug}: missing explicit {level.upper()} evidence"
                )
            for target in targets:
                path = target.get("file", "")
                test = target.get("test", "")
                if not path.startswith(prefix):
                    raise ValueError(
                        f"{slug}: {level} target must live under {prefix}: {path}"
                    )
                source = ROOT / path
                if not source.is_file():
                    raise ValueError(
                        f"{slug}: evidence source missing: {path}"
                    )
                if f"def {test}(" not in source.read_text(encoding="utf-8"):
                    raise ValueError(
                        f"{slug}: evidence test missing: {path}::{test}"
                    )


def evidence_for(
    slug: str,
    level: str,
) -> tuple[dict[str, str], ...]:
    return tuple(CASE_EVIDENCE[slug][level])
