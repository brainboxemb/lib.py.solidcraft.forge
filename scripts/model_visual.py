#!/usr/bin/env python3
"""Forge-owned SolidCraft visual rendering for model-local visual policy.

Generic normalization, regression, projection and expected-shape drawing stay
in released lib.py.cad.verification. This module owns only model policy loading,
SolidCraft camera conversion and the SolidCraft snapshot invocation.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import math
from numbers import Real
from pathlib import Path
import shutil
import subprocess
from typing import Any


VIEWS = {
    "front": (0.0, 0.0),
    "right": (-math.pi / 2.0, 0.0),
    "top": (0.0, math.pi / 2.0),
    "iso": (-math.pi / 4.0, math.radians(32.0)),
}


def _number(value: Any, name: str) -> float:
    """Return one finite numeric policy/evidence value."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_int(value: Any, name: str) -> int:
    """Return one positive integer."""

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _xyz(value: Any, name: str) -> tuple[float, float, float]:
    """Return one finite XYZ tuple."""

    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must contain three numbers")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must contain three numbers") from exc
    if len(values) != 3:
        raise ValueError(f"{name} must contain three numbers")
    return (
        _number(values[0], f"{name}[0]"),
        _number(values[1], f"{name}[1]"),
        _number(values[2], f"{name}[2]"),
    )


def load_visual_policy(path: Path) -> dict[str, Any]:
    """Load and validate one model-local visual policy object."""

    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ValueError(f"visual policy must use schema 1: {path}")

    views = value.get("views")
    if not isinstance(views, dict) or not views:
        raise ValueError("visual policy requires at least one view")
    for name, row in views.items():
        if name not in VIEWS:
            raise ValueError(f"unsupported visual view: {name}")
        if not isinstance(row, dict):
            raise ValueError(f"visual view must be an object: {name}")
        baseline = row.get("baseline")
        baseline_payload = row.get("baseline_payload")
        has_baseline = isinstance(baseline, str) and bool(baseline.strip())
        has_payload = (
            isinstance(baseline_payload, str)
            and bool(baseline_payload.strip())
        )
        if has_baseline == has_payload:
            raise ValueError(
                f"visual view requires exactly one baseline source: {name}"
            )

    expected_views = value.get("expected_views")
    if expected_views is None:
        expected_views = list(views)
    if not isinstance(expected_views, list) or not expected_views:
        raise ValueError("visual policy requires at least one expected-shape view")
    normalized_expected_views = []
    for name in expected_views:
        if not isinstance(name, str) or name not in VIEWS:
            raise ValueError(f"unsupported expected-shape view: {name}")
        if name in normalized_expected_views:
            raise ValueError(f"duplicate expected-shape view: {name}")
        normalized_expected_views.append(name)
    value["expected_views"] = normalized_expected_views

    features = value.get("expected_features", [])
    if not isinstance(features, list):
        raise ValueError("expected_features must be a list")
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ValueError(f"expected_features[{index}] must be an object")
        kind = feature.get("type")
        if kind not in ("through_hole", "through_slot", "through_path_slot"):
            raise ValueError(
                f"unsupported expected feature type at index {index}: {kind}"
            )

    render = value.get("render")
    if not isinstance(render, dict):
        raise ValueError("visual policy requires render settings")
    _positive_int(render.get("width"), "render width")
    _positive_int(render.get("height"), "render height")

    regression = value.get("regression")
    if not isinstance(regression, dict):
        raise ValueError("visual policy requires regression settings")
    _positive_int(regression.get("width"), "regression width")
    _positive_int(regression.get("height"), "regression height")
    threshold = _positive_int(
        regression.get("changed_pixel_threshold"),
        "changed_pixel_threshold",
    )
    if threshold > 255:
        raise ValueError("changed_pixel_threshold may not exceed 255")
    if _number(regression.get("max_mean_difference"), "max_mean_difference") < 0:
        raise ValueError("max_mean_difference may not be negative")
    fraction = _number(
        regression.get("max_changed_fraction"),
        "max_changed_fraction",
    )
    if not 0 <= fraction <= 1:
        raise ValueError("max_changed_fraction must be between 0 and 1")

    provenance = value.get("baseline_provenance")
    if not isinstance(provenance, dict) or provenance.get("approval") != "approved":
        raise ValueError("visual baselines must have explicit approved provenance")

    boxes = value.get("expected_boxes")
    if not isinstance(boxes, list) or not boxes:
        raise ValueError("visual policy requires expected_boxes")
    for index, box in enumerate(boxes):
        if not isinstance(box, dict):
            raise ValueError(f"expected_boxes[{index}] must be an object")
        _xyz(box.get("minimum"), f"expected_boxes[{index}].minimum")
        _xyz(box.get("maximum"), f"expected_boxes[{index}].maximum")

    return value


def model_bounds(
    measurements: Mapping[str, Any],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return the complete measured SolidCraft body envelope."""

    bodies = measurements.get("bodies")
    if not isinstance(bodies, list) or not bodies:
        raise ValueError("SolidCraft measurements require at least one body")

    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    for index, body in enumerate(bodies):
        if not isinstance(body, Mapping):
            raise ValueError(f"bodies[{index}] must be an object")
        bbox = body.get("bbox")
        if not isinstance(bbox, Mapping):
            raise ValueError(f"bodies[{index}].bbox must be an object")
        low = _xyz(bbox.get("min"), f"bodies[{index}].bbox.min")
        high = _xyz(bbox.get("max"), f"bodies[{index}].bbox.max")
        for axis in range(3):
            if high[axis] < low[axis]:
                raise ValueError(f"bodies[{index}] has inverted bounds")
            minimum[axis] = min(minimum[axis], low[axis])
            maximum[axis] = max(maximum[axis], high[axis])

    return tuple(minimum), tuple(maximum)


def solidcraft_camera(
    measurements: Mapping[str, Any],
    view: str,
) -> dict[str, Any]:
    """Build the historical deterministic SolidCraft orthographic camera."""

    if view not in VIEWS:
        raise ValueError(f"unsupported visual view: {view}")
    low, high = model_bounds(measurements)
    target = [(a + b) / 2.0 for a, b in zip(low, high)]
    spans = [b - a for a, b in zip(low, high)]
    size = max(max(spans), 1.0)
    yaw, pitch = VIEWS[view]
    return {
        "target": target,
        "yaw": yaw,
        "pitch": pitch,
        "roll": 0.0,
        "distance": size * 1.65,
        "fov": 0.0,
    }


def verification_camera_values(camera: Mapping[str, Any]) -> dict[str, Any]:
    """Translate a SolidCraft camera to released-library camera values."""

    target = _xyz(camera.get("target"), "camera target")
    yaw = _number(camera.get("yaw"), "camera yaw")
    pitch = _number(camera.get("pitch"), "camera pitch")
    distance = _number(camera.get("distance"), "camera distance")
    if distance <= 0:
        raise ValueError("camera distance must be positive")
    return {
        "target": target,
        "yaw_deg": math.degrees(yaw),
        "pitch_deg": -math.degrees(pitch),
        "distance": 0.4 * distance,
    }


def _verification_camera(camera: Mapping[str, Any]):
    """Construct the generic released-library camera lazily in the runtime."""

    from cad_verification import OrthographicCamera

    return OrthographicCamera(**verification_camera_values(camera))


def _expected_boxes(policy: Mapping[str, Any]):
    """Construct released generic expected boxes from model-local data."""

    from cad_verification import ExpectedBox

    return tuple(
        ExpectedBox(
            minimum=_xyz(row["minimum"], "expected box minimum"),
            maximum=_xyz(row["maximum"], "expected box maximum"),
            label=row.get("label"),
        )
        for row in policy["expected_boxes"]
    )


def _expected_features(policy: Mapping[str, Any]):
    """Construct released generic expected features from model-local data."""

    from cad_verification import ThroughHole, ThroughPathSlot, ThroughSlot

    result = []
    for index, row in enumerate(policy.get("expected_features", [])):
        kind = row.get("type")
        label = row.get("label")
        z = row.get("z")
        if not isinstance(z, list) or len(z) != 2:
            raise ValueError(f"expected_features[{index}].z must contain two numbers")
        z_min = _number(z[0], f"expected_features[{index}].z[0]")
        z_max = _number(z[1], f"expected_features[{index}].z[1]")

        if kind == "through_hole":
            center = row.get("center")
            if not isinstance(center, list) or len(center) != 2:
                raise ValueError(
                    f"expected_features[{index}].center must contain two numbers"
                )
            result.append(
                ThroughHole(
                    center=(
                        _number(center[0], f"expected_features[{index}].center[0]"),
                        _number(center[1], f"expected_features[{index}].center[1]"),
                    ),
                    diameter=_number(
                        row.get("diameter"),
                        f"expected_features[{index}].diameter",
                    ),
                    z_min=z_min,
                    z_max=z_max,
                    label=label,
                )
            )
            continue

        centerline = row.get("centerline")
        if not isinstance(centerline, list):
            raise ValueError(
                f"expected_features[{index}].centerline must be a list"
            )
        points = []
        for point_index, point in enumerate(centerline):
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError(
                    f"expected_features[{index}].centerline[{point_index}] "
                    "must contain two numbers"
                )
            points.append(
                (
                    _number(
                        point[0],
                        f"expected_features[{index}].centerline[{point_index}][0]",
                    ),
                    _number(
                        point[1],
                        f"expected_features[{index}].centerline[{point_index}][1]",
                    ),
                )
            )
        width = _number(
            row.get("width"),
            f"expected_features[{index}].width",
        )
        if kind == "through_slot":
            if len(points) != 2:
                raise ValueError(
                    f"expected_features[{index}] straight slot requires two "
                    "centerline points"
                )
            result.append(
                ThroughSlot(
                    start=points[0],
                    end=points[1],
                    width=width,
                    z_min=z_min,
                    z_max=z_max,
                    label=label,
                )
            )
        else:
            result.append(
                ThroughPathSlot(
                    centerline=tuple(points),
                    width=width,
                    z_min=z_min,
                    z_max=z_max,
                    label=label,
                )
            )
    return tuple(result)


def _reference(path: Path, output_dir: Path) -> str:
    """Return one output-root-relative artifact reference."""

    return path.resolve().relative_to(output_dir.resolve()).as_posix()


def _snapshot(
    model_path: Path,
    output_path: Path,
    camera: Mapping[str, Any],
    *,
    width: int,
    height: int,
) -> None:
    """Render one deterministic SolidCraft PNG."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "solidcraft-cli",
            "snapshot",
            str(model_path),
            "--out",
            str(output_path),
            "--width",
            str(width),
            "--height",
            str(height),
            "--camera",
            json.dumps(camera, separators=(",", ":")),
            "--no-grid",
            "--no-axes",
        ],
        check=True,
    )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"SolidCraft snapshot is missing or empty: {output_path}")



def _baseline_source(
    policy_path: Path,
    view_policy: Mapping[str, Any],
    view_root: Path,
) -> tuple[Path, str]:
    """Return one approved baseline image, decoding payloads through the library."""

    baseline = view_policy.get("baseline")
    if isinstance(baseline, str) and baseline.strip():
        return policy_path.parent / baseline, baseline

    payload_reference = view_policy["baseline_payload"]
    payload_path = policy_path.parent / payload_reference
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("approval") != "approved":
        raise ValueError(
            f"encoded baseline must have approved provenance: {payload_path}"
        )

    from cad_verification import decode_baseline

    image = decode_baseline(payload)
    materialized = view_root / "approved-baseline.png"
    image.save(
        materialized,
        format="PNG",
        optimize=False,
        compress_level=9,
    )
    return materialized, payload_reference

def _view_status(
    evidence: Mapping[str, Any],
    *,
    regression_required: bool,
    expected_shape_required: bool,
) -> str:
    """Return status from only the verification roles required for one view."""

    states = []
    if regression_required:
        states.append(evidence.get("baseline_status"))
    if expected_shape_required:
        states.append(evidence.get("expected_shape_status"))
    for status in ("error", "fail", "missing", "review"):
        if status in states:
            return status
    return "pass"


def write_presentation_preview(
    model_path: Path,
    measurements_path: Path,
    output_dir: Path,
    *,
    width: int = 720,
    height: int = 540,
) -> dict[str, Any]:
    """Write one current ISO preview without creating verification status."""

    model_path = Path(model_path).resolve()
    measurements_path = Path(measurements_path).resolve()
    output_dir = Path(output_dir).resolve()
    width = _positive_int(width, "presentation preview width")
    height = _positive_int(height, "presentation preview height")

    measurements = json.loads(measurements_path.read_text(encoding="utf-8"))
    if not isinstance(measurements, dict):
        raise ValueError("baseline measurements must contain one object")
    camera = solidcraft_camera(measurements, "iso")

    presentation = output_dir / "presentation"
    presentation.mkdir(parents=True, exist_ok=True)
    preview = presentation / "preview-iso.png"
    current_iso = output_dir / "visual" / "iso" / "actual.png"

    if current_iso.is_file() and current_iso.stat().st_size > 0:
        shutil.copyfile(current_iso, preview)
        renderer = "reused-visual"
        source = _reference(current_iso, output_dir)
    else:
        _snapshot(
            model_path,
            preview,
            camera,
            width=width,
            height=height,
        )
        renderer = "solidcraft-snapshot"
        source = _reference(model_path, output_dir)

    metadata = {
        "schema": 1,
        "kind": "presentation-preview",
        "renderer": renderer,
        "view": "iso",
        "image": "preview-iso.png",
        "source": source,
        "width": width,
        "height": height,
        "camera": camera,
    }
    (presentation / "preview.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def run_visual_verification(
    model_path: Path,
    measurements_path: Path,
    policy_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Render and verify all model-required visual views."""

    from cad_verification import (
        SemanticCheck,
        VerificationFailure,
        compose_semantic_result,
        verify_visual_view,
    )

    model_path = Path(model_path).resolve()
    measurements_path = Path(measurements_path).resolve()
    policy_path = Path(policy_path).resolve()
    output_dir = Path(output_dir).resolve()

    policy = load_visual_policy(policy_path)
    measurements = json.loads(measurements_path.read_text(encoding="utf-8"))
    if not isinstance(measurements, dict):
        raise ValueError("baseline measurements must contain one object")

    render = policy["render"]
    regression = policy["regression"]
    boxes = _expected_boxes(policy)
    features = _expected_features(policy)
    regression_views = policy["views"]
    expected_views = tuple(policy["expected_views"])
    render_views = tuple(
        dict.fromkeys((*regression_views.keys(), *expected_views))
    )
    visual_root = output_dir / "visual"
    visual_root.mkdir(parents=True, exist_ok=True)

    checks = []
    views = []
    for view_name in render_views:
        view_policy = regression_views.get(view_name)
        regression_required = view_policy is not None
        expected_shape_required = view_name in expected_views
        view_root = visual_root / view_name
        view_root.mkdir(parents=True, exist_ok=True)

        camera = solidcraft_camera(measurements, view_name)
        camera_path = view_root / "camera.json"
        camera_path.write_text(
            json.dumps(camera, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        actual_path = view_root / "actual.png"
        _snapshot(
            model_path,
            actual_path,
            camera,
            width=render["width"],
            height=render["height"],
        )

        if regression_required:
            baseline_path, baseline_reference = _baseline_source(
                policy_path,
                view_policy,
                view_root,
            )
            diff_path = view_root / "diff.png"
            diff_reference = _reference(diff_path, output_dir)
        else:
            baseline_path = None
            baseline_reference = None
            diff_path = None
            diff_reference = None

        if expected_shape_required:
            goal_path = view_root / "goal.png"
            overlay_path = view_root / "overlay.png"
            verification_camera = _verification_camera(camera)
            expected_boxes = boxes
            expected_features = features
            goal_reference = _reference(goal_path, output_dir)
            overlay_reference = _reference(overlay_path, output_dir)
        else:
            goal_path = None
            overlay_path = None
            verification_camera = None
            expected_boxes = ()
            expected_features = ()
            goal_reference = None
            overlay_reference = None

        try:
            visual = verify_visual_view(
                actual_path,
                actual_reference=_reference(actual_path, output_dir),
                baseline_path=baseline_path,
                normalized_size=(
                    regression["width"],
                    regression["height"],
                ),
                changed_pixel_threshold=regression["changed_pixel_threshold"],
                max_mean_difference=regression["max_mean_difference"],
                max_changed_fraction=regression["max_changed_fraction"],
                diff_path=diff_path,
                diff_reference=diff_reference,
                camera=verification_camera,
                boxes=expected_boxes,
                features=expected_features,
                goal_path=goal_path,
                goal_reference=goal_reference,
                overlay_path=overlay_path,
                overlay_reference=overlay_reference,
            )
            evidence = visual.to_evidence()
            status = _view_status(
                evidence,
                regression_required=regression_required,
                expected_shape_required=expected_shape_required,
            )
        except VerificationFailure as exc:
            evidence = (
                dict(exc.evidence)
                if isinstance(exc.evidence, Mapping)
                else {"error": str(exc)}
            )
            status = "fail"

        row = {
            "view": view_name,
            "status": status,
            "regression_required": regression_required,
            "expected_shape_required": expected_shape_required,
            "camera": _reference(camera_path, output_dir),
            "baseline": baseline_reference,
            "evidence": evidence,
        }
        views.append(row)
        checks.append(
            SemanticCheck(
                name=view_name,
                status=status,
                required=True,
                evidence=row,
            )
        )

    semantic = compose_semantic_result(checks)
    report = {
        "schema": "forge-visual-verification",
        "schema_version": 1,
        "status": semantic["status"],
        "baseline_provenance": policy["baseline_provenance"],
        "views": views,
        "semantic": semantic,
    }
    (output_dir / "visual.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
