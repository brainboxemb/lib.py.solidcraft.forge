#!/usr/bin/env python3
"""Forge-owned SolidCraft rendering adapter for visual verification.

This module owns only Forge/SolidCraft policy:
- deterministic model cameras derived from measured bounds;
- invoking SolidCraft snapshot rendering;
- loading model-local visual configuration and approved baselines.

Generic normalization, regression comparison, projection, expected geometry
drawing and structured visual evidence come from lib.py.cad.verfication.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image

from cad_verification import (
    ExpectedBox,
    OrthographicCamera,
    VerificationFailure,
    VisualViewEvidence,
    compare_images,
    make_goal_image,
    make_overlay_image,
    normalize_image,
    run_command,
    write_diff_image,
)


SOLIDCRAFT_VIEWS = {
    "front": (0.0, 0.0),
    "right": (-90.0, 0.0),
    "top": (0.0, 90.0),
    "iso": (-45.0, 32.0),
}


def load_json(path: Path) -> dict[str, Any]:
    """Read one required JSON object."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def model_envelope(measurements: dict[str, Any]) -> tuple[list[float], list[float]]:
    """Return the total measured body envelope."""

    bodies = measurements.get("bodies", [])
    if not isinstance(bodies, list) or not bodies:
        raise ValueError("measurement JSON contains no bodies")

    minimum = [
        min(float(body["bbox"]["min"][axis]) for body in bodies)
        for axis in range(3)
    ]
    maximum = [
        max(float(body["bbox"]["max"][axis]) for body in bodies)
        for axis in range(3)
    ]
    return minimum, maximum


def solidcraft_camera(
    measurements: dict[str, Any],
    view: str,
) -> dict[str, Any]:
    """Build one deterministic SolidCraft orthographic camera."""

    if view not in SOLIDCRAFT_VIEWS:
        raise ValueError(f"unsupported visual view: {view}")

    minimum, maximum = model_envelope(measurements)
    target = [
        (low + high) / 2.0
        for low, high in zip(minimum, maximum)
    ]
    spans = [
        high - low
        for low, high in zip(minimum, maximum)
    ]
    size = max(max(spans), 1.0)
    yaw_deg, pitch_deg = SOLIDCRAFT_VIEWS[view]

    return {
        "target": target,
        "yaw": math.radians(yaw_deg),
        "pitch": math.radians(pitch_deg),
        "roll": 0.0,
        "distance": size * 1.65,
        "fov": 0.0,
    }


def verification_camera(camera: dict[str, Any]) -> OrthographicCamera:
    """Convert a SolidCraft camera to the library's projection convention."""

    return OrthographicCamera(
        target=tuple(float(value) for value in camera["target"]),
        yaw_deg=math.degrees(float(camera["yaw"])),
        # SolidCraft positive pitch looks down while the generic projection
        # helper uses the opposite sign for the equivalent orthographic view.
        pitch_deg=-math.degrees(float(camera["pitch"])),
        # SolidCraft orthographic half-height is 0.4 * camera distance.
        distance=0.4 * float(camera["distance"]),
    )


def expected_boxes(config: dict[str, Any]) -> tuple[ExpectedBox, ...]:
    """Load model-local expected boxes for independent goal/overlay evidence."""

    rows = config.get("expected_boxes", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("visual config requires expected_boxes")

    return tuple(
        ExpectedBox(
            minimum=tuple(row["minimum"]),
            maximum=tuple(row["maximum"]),
            label=row.get("label"),
        )
        for row in rows
    )


def _relative(path: Path, root: Path) -> str:
    """Return one stable POSIX-style evidence path."""

    return path.resolve().relative_to(root.resolve()).as_posix()


def verify_visual(
    *,
    model: Path,
    measurements_path: Path,
    config_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Render and verify every model-local required visual view."""

    model = model.resolve()
    measurements_path = measurements_path.resolve()
    config_path = config_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    measurements = load_json(measurements_path)
    config = load_json(config_path)
    if config.get("schema") != 1:
        raise ValueError("unsupported visual config schema")

    views = config.get("views")
    if not isinstance(views, dict) or not views:
        raise ValueError("visual config requires at least one view")

    render = config["render"]
    render_width = int(render["width"])
    render_height = int(render["height"])
    regression = config["regression"]
    normal_width = int(regression["width"])
    normal_height = int(regression["height"])
    boxes = expected_boxes(config)

    view_results: dict[str, Any] = {}
    overall = "pass"

    for view, view_config in views.items():
        if not isinstance(view_config, dict):
            raise ValueError(f"visual view config must be an object: {view}")

        camera = solidcraft_camera(measurements, view)
        camera_path = output_dir / f"camera-{view}.json"
        camera_path.write_text(
            json.dumps(camera, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        actual_path = output_dir / f"actual-{view}.png"
        run_command(
            [
                "solidcraft-cli",
                "snapshot",
                str(model),
                "--out",
                str(actual_path),
                "--width",
                str(render_width),
                "--height",
                str(render_height),
                "--camera",
                json.dumps(camera, separators=(",", ":")),
                "--no-grid",
                "--no-axes",
            ]
        )

        current = normalize_image(
            actual_path,
            normal_width,
            normal_height,
        )
        baseline_value = view_config.get("baseline")
        baseline_path = (
            config_path.parent / str(baseline_value)
            if baseline_value
            else None
        )

        baseline_status = "missing"
        regression_evidence = None
        diff_path = None

        if baseline_path is not None and baseline_path.is_file():
            reference = normalize_image(
                baseline_path,
                normal_width,
                normal_height,
            )
            diff_path = output_dir / f"diff-{view}.png"
            write_diff_image(current, reference, diff_path)
            try:
                regression_evidence = compare_images(
                    current,
                    reference,
                    changed_pixel_threshold=int(
                        regression["changed_pixel_threshold"]
                    ),
                    max_mean_difference=float(
                        regression["max_mean_difference"]
                    ),
                    max_changed_fraction=float(
                        regression["max_changed_fraction"]
                    ),
                )
                baseline_status = "pass"
            except VerificationFailure as exc:
                regression_evidence = dict(exc.evidence)
                baseline_status = "fail"
                overall = "fail"
        else:
            overall = "missing"

        projection = verification_camera(camera)
        goal = make_goal_image(
            (render_width, render_height),
            projection,
            boxes=boxes,
            labels=True,
            fill=True,
        )
        goal_path = output_dir / f"goal-{view}.png"
        goal.save(goal_path, format="PNG", optimize=False, compress_level=9)

        with Image.open(actual_path) as image:
            image.load()
            overlay = make_overlay_image(
                image.convert("RGB"),
                projection,
                boxes=boxes,
                labels=False,
                fill=False,
            )
        overlay_path = output_dir / f"overlay-{view}.png"
        overlay.save(
            overlay_path,
            format="PNG",
            optimize=False,
            compress_level=9,
        )

        evidence = VisualViewEvidence(
            actual_image=_relative(actual_path, output_dir),
            baseline_status=baseline_status,
            regression=regression_evidence,
            diff_image=(
                _relative(diff_path, output_dir)
                if diff_path is not None
                else None
            ),
            goal_image=_relative(goal_path, output_dir),
            overlay_image=_relative(overlay_path, output_dir),
            # This status means the declared independent expected geometry was
            # successfully projected and emitted as goal/overlay evidence.
            # Native geometry and pixel regression remain separate checks.
            expected_shape_status="pass",
        ).to_evidence()
        evidence["camera"] = _relative(camera_path, output_dir)
        evidence["baseline"] = (
            str(baseline_path.relative_to(config_path.parent))
            if baseline_path is not None
            else None
        )
        view_results[view] = evidence

    report = {
        "schema": 1,
        "status": overall,
        "baseline_provenance": config.get("baseline_provenance", {}),
        "views": view_results,
    }
    report_path = output_dir / "visual-verification.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
