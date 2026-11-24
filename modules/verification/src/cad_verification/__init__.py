"""Reusable CAD/model verification library."""

from importlib import import_module

from .adapters import (
    SolidCraftBodyExpectation,
    SolidCraftBodyGroupExpectation,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftInspectionSelect,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    SolidCraftVerification,
    evaluate_solidcraft_model,
    inspect_solidcraft_model,
    load_solidcraft_verification,
    mutate_solidcraft_model,
    run_solidcraft_verification,
    run_solidcraft_verification_file,
    verify_solidcraft_measurements,
)
from .assertions import (
    require_condition,
    require_equal,
)
from .comparison import (
    BodyEnvelope,
    compare_bounds,
    compare_scalar,
    compare_vector,
    match_body_envelopes,
)
from .errors import (
    ArtifactError,
    CommandError,
    CommandFailed,
    CommandTimedOut,
    MeshLoadError,
    SemanticResultError,
    SolidCraftEvidenceError,
    VerificationConfigError,
    VerificationError,
    VerificationFailure,
    VisualEvidenceError,
)
from .model import (
    CheckOutcome,
    CommandResult,
    VerificationCheck,
    VerificationContext,
)
from .process import run_command
from .semantic import (
    SemanticCheck,
    compose_item_results,
    compose_semantic_result,
    require_semantic_pass,
    semantic_checks_from_report,
)
from .verification import verify


_LAZY_EXPORTS = {
    "GeometryContract": (".geometry", "GeometryContract"),
    "geometry_contract_from_mapping": (".geometry", "geometry_contract_from_mapping"),
    "load_geometry_contract": (".geometry", "load_geometry_contract"),
    "run_mesh_geometry_verification": (".geometry", "run_mesh_geometry_verification"),
    "SurfaceDistanceProbe": (".geometry", "SurfaceDistanceProbe"),
    "validate_mesh_geometry": (".geometry", "validate_mesh_geometry"),
    "ExpectedBox": (".visual", "ExpectedBox"),
    "OrthographicCamera": (".visual", "OrthographicCamera"),
    "ThroughHole": (".visual", "ThroughHole"),
    "ThroughSlot": (".visual", "ThroughSlot"),
    "ThroughPathSlot": (".visual", "ThroughPathSlot"),
    "VisualViewEvidence": (".visual", "VisualViewEvidence"),
    "compare_images": (".visual", "compare_images"),
    "decode_baseline": (".visual", "decode_baseline"),
    "draw_expected_geometry": (".visual", "draw_expected_geometry"),
    "encode_baseline": (".visual", "encode_baseline"),
    "make_goal_image": (".visual", "make_goal_image"),
    "make_overlay_image": (".visual", "make_overlay_image"),
    "normalize_image": (".visual", "normalize_image"),
    "project_points": (".visual", "project_points"),
    "verify_visual_view": (".visual", "verify_visual_view"),
    "write_diff_image": (".visual", "write_diff_image"),
}


def __getattr__(name: str):
    """Load optional geometry/visual public APIs only when requested."""

    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute = target
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Include lazy public exports in normal module introspection."""

    return sorted(set(globals()) | set(__all__))

__all__ = [
    "ArtifactError",
    "BodyEnvelope",
    "CheckOutcome",
    "CommandError",
    "CommandFailed",
    "CommandResult",
    "CommandTimedOut",
    "ExpectedBox",
    "GeometryContract",
    "OrthographicCamera",
    "MeshLoadError",
    "SemanticCheck",
    "SemanticResultError",
    "SolidCraftBodyExpectation",
    "SolidCraftBodyGroupExpectation",
    "SolidCraftEvidenceError",
    "SolidCraftInspection",
    "SolidCraftInspectionCheck",
    "SolidCraftInspectionSelect",
    "SolidCraftMeasurementChangeExpectation",
    "SolidCraftModelExpectation",
    "SolidCraftSavedDesign",
    "SolidCraftSketchExpectation",
    "SolidCraftTimelineExpectation",
    "SolidCraftVerification",
    "VerificationCheck",
    "VerificationConfigError",
    "VerificationContext",
    "VerificationError",
    "VerificationFailure",
    "SurfaceDistanceProbe",
    "ThroughHole",
    "ThroughSlot",
    "ThroughPathSlot",
    "VisualEvidenceError",
    "VisualViewEvidence",
    "compare_bounds",
    "compare_images",
    "compose_item_results",
    "compose_semantic_result",
    "compare_scalar",
    "compare_vector",
    "decode_baseline",
    "draw_expected_geometry",
    "encode_baseline",
    "evaluate_solidcraft_model",
    "make_goal_image",
    "make_overlay_image",
    "match_body_envelopes",
    "mutate_solidcraft_model",
    "normalize_image",
    "run_solidcraft_verification",
    "run_solidcraft_verification_file",
    "run_mesh_geometry_verification",
    "project_points",
    "require_condition",
    "require_equal",
    "inspect_solidcraft_model",
    "load_geometry_contract",
    "load_solidcraft_verification",
    "geometry_contract_from_mapping",
    "require_semantic_pass",
    "semantic_checks_from_report",
    "run_command",
    "validate_mesh_geometry",
    "verify",
    "verify_solidcraft_measurements",
    "verify_visual_view",
    "write_diff_image",
]
