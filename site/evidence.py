"""Resolve per-case generated build evidence for the public site."""

MODEL_VERIFICATION_LEVELS = frozenset(
    {"model_verify", "tool_qualification"}
)


def scpf_case_state(build_manifest_data, slug, *, fallback_verified=False):
    """Return the SCPF build record and whether it carries model verification."""
    record = (
        ((build_manifest_data.get("cases") or {}).get(slug) or {})
        .get("implementations", {})
        .get("scpf")
    )
    if build_manifest_data:
        verified = bool(
            record
            and record.get("status") == "pass"
            and record.get("verification_level") in MODEL_VERIFICATION_LEVELS
        )
    else:
        verified = bool(fallback_verified)
    return record, verified
