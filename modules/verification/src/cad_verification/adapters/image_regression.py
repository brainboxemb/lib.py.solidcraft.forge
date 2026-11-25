"""Generic approved-image regression adapter.

The producer owns rendering. This adapter only compares an already-produced
image artifact with a consumer-approved baseline using cad_verification's
released visual primitives.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any

from ..errors import VerificationFailure
from ..evidence import artifact_record


def _load_policy(path: Path) -> dict[str, Any]:
    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError(f"image regression policy must use schema 1: {path}")

    baseline = value.get("baseline_payload")
    if not isinstance(baseline, str) or not baseline.strip():
        raise ValueError("image regression requires baseline_payload")
    relative = Path(baseline)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("baseline_payload must be a policy-relative path")

    size = value.get("normalized_size")
    if (
        not isinstance(size, list)
        or len(size) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in size)
    ):
        raise ValueError("normalized_size must contain two positive integers")

    provenance = value.get("baseline_provenance")
    if not isinstance(provenance, dict) or provenance.get("approval") != "approved":
        raise ValueError("image regression baseline must have approved provenance")

    return value


def run_image_regression_verification_file(
    image_path: Path,
    output_dir: Path,
    policy_path: Path,
    *,
    verification_id: str,
) -> dict[str, Any]:
    """Compare one existing image artifact with an approved baseline."""

    from cad_verification import decode_baseline, verify_visual_view

    image_path = Path(image_path).resolve()
    output_dir = Path(output_dir).resolve()
    policy_path = Path(policy_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not image_path.is_file() or image_path.stat().st_size == 0:
        raise ValueError(f"image regression input is missing or empty: {image_path}")

    policy = _load_policy(policy_path)
    baseline_payload_path = (
        policy_path.parent / policy["baseline_payload"]
    ).resolve()
    try:
        baseline_payload_path.relative_to(policy_path.parent.resolve())
    except ValueError as exc:
        raise ValueError("baseline payload escapes policy directory") from exc

    payload = json.loads(baseline_payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("approval") != "approved":
        raise ValueError(
            f"baseline payload must have approved provenance: {baseline_payload_path}"
        )

    actual = output_dir / "actual.png"
    baseline = output_dir / "approved-baseline.png"
    diff = output_dir / "diff.png"
    shutil.copyfile(image_path, actual)
    decoded = decode_baseline(payload)
    decoded.save(
        baseline,
        format="PNG",
        optimize=False,
        compress_level=9,
    )

    evidence: dict[str, Any]
    status = "pass"
    error = None
    try:
        visual = verify_visual_view(
            actual,
            actual_reference="actual.png",
            baseline_path=baseline,
            normalized_size=tuple(policy["normalized_size"]),
            changed_pixel_threshold=policy["changed_pixel_threshold"],
            max_mean_difference=policy["max_mean_difference"],
            max_changed_fraction=policy["max_changed_fraction"],
            diff_path=diff,
            diff_reference="diff.png",
        )
        evidence = visual.to_evidence()
    except VerificationFailure as exc:
        status = "fail"
        error = str(exc)
        evidence = (
            dict(exc.evidence)
            if isinstance(exc.evidence, dict)
            else {"error": str(exc)}
        )

    artifacts = [
        artifact_record(actual, output_dir),
        artifact_record(baseline, output_dir),
    ]
    if diff.is_file():
        artifacts.append(artifact_record(diff, output_dir))

    report = {
        "schema": "cad-verification",
        "schema_version": 1,
        "verification_id": verification_id,
        "status": status,
        "input": str(image_path),
        "metadata": {
            "kind": "image-regression",
            "baseline_payload": policy["baseline_payload"],
            "baseline_provenance": policy["baseline_provenance"],
        },
        "checks": [
            {
                "id": "image-regression",
                "status": status,
                "reason": None,
                "error": error,
                "evidence": evidence,
                "artifacts": artifacts,
            }
        ],
    }
    (output_dir / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
