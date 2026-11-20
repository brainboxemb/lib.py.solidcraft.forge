"""Build presentation-neutral view data from accepted stable evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from build_evidence import ExampleBuildEvidence, StableBuildEvidence


LIBRARY_URL = "https://github.com/brainboxemb/lib.py.solidcraft.forge"


def _json_text(value: Any) -> str:
    """Return deterministic readable JSON for exact machine evidence."""
    return json.dumps(value, indent=2, sort_keys=True)


def _source_url(commit: str, path: str) -> str:
    """Return one immutable Forge source link."""
    return f"{LIBRARY_URL}/blob/{commit}/{path}"


def _artifact_url(
    stable: StableBuildEvidence,
    path: Path,
    *,
    raw: bool = False,
) -> str:
    """Return one immutable durable-build artifact link."""
    return stable.raw_url(path) if raw else stable.blob_url(path)


def _parameter_rows(measurements: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Normalize editable SolidCraft parameters for one table."""
    rows = []
    for row in measurements.get("params", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "name": row.get("name"),
                "value": row.get("value"),
                "unit": row.get("unit") or "",
                "expression": row.get("expression"),
            }
        )
    return tuple(rows)


def _body_rows(measurements: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Normalize measured native bodies without changing numeric values."""
    rows = []
    for row in measurements.get("bodies", []):
        if not isinstance(row, dict):
            continue
        bbox = row.get("bbox") if isinstance(row.get("bbox"), dict) else {}
        rows.append(
            {
                "name": row.get("name") or "(unnamed)",
                "minimum": bbox.get("min"),
                "maximum": bbox.get("max"),
                "volume_mm3": row.get("volume_mm3"),
                "faces": row.get("faces"),
                "edges": row.get("edges"),
                "closed": row.get("closed"),
            }
        )
    return tuple(rows)


def _verification_rows(report: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    """Expose exact verification checks as status plus unmodified evidence JSON."""
    rows = []
    for row in report.get("checks", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "id": row.get("id"),
                "status": row.get("status"),
                "reason": row.get("reason"),
                "evidence_json": _json_text(row.get("evidence") or {}),
            }
        )
    return tuple(rows)


def _saved_design_rows(
    stable: StableBuildEvidence,
    example: ExampleBuildEvidence,
) -> tuple[dict[str, Any], ...]:
    """Expose current saved-design measurements and immutable raw links."""
    rows = []
    for name, path, measurements in example.saved_designs:
        rows.append(
            {
                "name": name,
                "measurements_json": _json_text(measurements),
                "measurements_url": _artifact_url(stable, path),
            }
        )
    return tuple(rows)


def _visual_rows(
    stable: StableBuildEvidence,
    example: ExampleBuildEvidence,
) -> tuple[dict[str, Any], ...]:
    """Expose current visual verification views only when they exist."""
    if example.visual is None or example.visual_path is None:
        return ()

    root = example.visual_path.parent
    rows = []
    for row in example.visual.get("views", []):
        if not isinstance(row, dict):
            continue
        evidence = row.get("evidence")
        if not isinstance(evidence, dict):
            continue

        def image_url(key: str) -> str | None:
            relative = evidence.get(key)
            if not isinstance(relative, str):
                return None
            return _artifact_url(stable, root / relative, raw=True)

        rows.append(
            {
                "view": row.get("view"),
                "status": row.get("status"),
                "baseline_status": evidence.get("baseline_status"),
                "expected_shape_status": evidence.get("expected_shape_status"),
                "actual_url": image_url("actual_image"),
                "goal_url": image_url("goal_image"),
                "overlay_url": image_url("overlay_image"),
                "diff_url": image_url("diff_image"),
                "regression_json": _json_text(evidence.get("regression") or {}),
            }
        )
    return tuple(rows)


def _reference_rows(
    stable: StableBuildEvidence,
    example: ExampleBuildEvidence,
) -> tuple[dict[str, Any], ...]:
    """Expose each canonical independent reference child."""
    rows = []
    for reference in example.references:
        source = reference.verification.get("source")
        rows.append(
            {
                "implementation": reference.implementation,
                "status": reference.verification.get("status"),
                "accepted_source_commit": reference.item.source_commit,
                "source_url": (
                    _source_url(reference.item.source_commit, source)
                    if isinstance(source, str)
                    else None
                ),
                "preview_url": _artifact_url(
                    stable,
                    reference.preview_path,
                    raw=True,
                ),
                "preview_metadata_url": _artifact_url(
                    stable,
                    reference.preview_path.parent / "preview.json",
                ),
                "stl_url": _artifact_url(stable, reference.stl_path),
                "verification_url": _artifact_url(
                    stable,
                    reference.stl_path.parent / "verification.json",
                ),
                "geometry_json": _json_text(
                    reference.verification.get("geometry") or {}
                ),
            }
        )
    return tuple(rows)


def qualification_case_view(
    stable: StableBuildEvidence,
    example: ExampleBuildEvidence,
    summary: dict[str, Any],
    *,
    site_source_commit: str,
) -> dict[str, Any]:
    """Build one qualification page view-model from current source/evidence."""
    return {
        "slug": example.slug,
        "status": summary.get("status"),
        "checks": summary.get("checks") or {},
        "site_source_commit": site_source_commit,
        "accepted_source_commit": example.item.source_commit,
        "build_commit": stable.build_commit,
        "preview_url": _artifact_url(stable, example.preview_path, raw=True),
        "preview_metadata_url": _artifact_url(
            stable,
            example.preview_path.parent / "preview.json",
        ),
        "model_source_url": _source_url(
            example.item.source_commit,
            f"examples/{example.slug}/scpf/model.py",
        ),
        "verification_source_url": _source_url(
            site_source_commit,
            f"examples/{example.slug}/verification/verify.py",
        ),
        "commands_url": _artifact_url(stable, example.command_path),
        "verification_url": _artifact_url(stable, example.verification_path),
        "measurements_url": _artifact_url(stable, example.measurements_path),
        "native_model_url": _artifact_url(stable, example.native_model_path),
        "native_step_url": _artifact_url(stable, example.native_step_path),
        "native_results_url": _artifact_url(stable, example.native_results_path),
        "parameters": _parameter_rows(example.measurements),
        "bodies": _body_rows(example.measurements),
        "verification_checks": _verification_rows(example.verification),
        "saved_designs": _saved_design_rows(stable, example),
        "visual_views": _visual_rows(stable, example),
        "references": _reference_rows(stable, example),
    }


def diagram_views(stable: StableBuildEvidence) -> tuple[dict[str, Any], ...]:
    """Expose CADCraft diagrams from their durable provenance rows."""
    by_name = {path.name: path for path in stable.diagram_paths}
    rows = []
    for row in stable.diagram_provenance.get("diagrams", []):
        if not isinstance(row, dict) or row.get("status") != "pass":
            continue
        svg = row.get("svg")
        if not isinstance(svg, str):
            continue
        path = by_name.get(Path(svg).name)
        if path is None:
            continue
        rows.append(
            {
                "name": row.get("name"),
                "title": row.get("title") or row.get("name"),
                "svg_url": _artifact_url(stable, path, raw=True),
                "svg_evidence_url": _artifact_url(stable, path),
                "source": row.get("source"),
                "cadcraft_version": stable.diagram_provenance.get(
                    "cadcraft_version"
                ),
            }
        )
    return tuple(rows)
