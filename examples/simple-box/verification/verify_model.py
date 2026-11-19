#!/usr/bin/env python3
"""Verify the simple-box SolidCraft model and its saved-design editability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

from cad_verification import (
    CheckOutcome,
    VerificationCheck,
    VerificationContext,
    VerificationFailure,
    run_command,
    verify,
)
from scpf.headless import run_document


EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verification.visual_validation import verify_visual
MODEL_METADATA = EXAMPLE / "model.yml"
MUTATION = EXAMPLE / "verification" / "change_length.json"
VISUAL_CONFIG = EXAMPLE / "verification" / "visual.json"
MODEL_FIELDS = {
    "section",
    "title",
    "tagline",
    "description",
    "parameters",
    "stages",
}


def model_metadata() -> dict[str, Any]:
    """Load the generic model/Page labels and reject accidental extra schemas."""

    value = yaml.safe_load(MODEL_METADATA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("model.yml must contain one mapping")
    if set(value) != MODEL_FIELDS:
        raise ValueError(
            "model.yml fields must be exactly: "
            + ", ".join(sorted(MODEL_FIELDS))
        )
    if not isinstance(value["stages"], list) or not value["stages"]:
        raise ValueError("model.yml stages must be a non-empty list")
    return value


def load_json(path: Path) -> dict[str, Any]:
    """Read one SolidCraft measurement object."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def parameters(data: dict[str, Any]) -> dict[str, float]:
    """Return native parameter values keyed by parameter name."""

    return {
        str(row["name"]): float(row["value"])
        for row in data.get("params", [])
    }


def box_bounds(data: dict[str, Any]) -> dict[str, list[float]] | None:
    """Return the first body's measured bounds when one body exists."""

    bodies = data.get("bodies", [])
    if not isinstance(bodies, list) or len(bodies) != 1:
        return None
    bbox = bodies[0].get("bbox")
    return bbox if isinstance(bbox, dict) else None


def normalized_bounds(
    value: dict[str, list[float]] | None,
) -> dict[str, list[float]] | None:
    """Round measured bounds to stable engineering precision."""

    if value is None:
        return None
    return {
        key: [round(float(number), 6) for number in value[key]]
        for key in ("min", "max")
    }


def require_equal(
    label: str,
    actual: Any,
    expected: Any,
) -> None:
    """Raise an expected verification failure for one model mismatch."""

    if actual != expected:
        raise VerificationFailure(
            label,
            evidence={
                "expected": expected,
                "actual": actual,
            },
        )


def replay_check(ctx: VerificationContext) -> CheckOutcome:
    """Replay the Forge command document into an editable SolidCraft model."""

    document = load_json(ctx.input_path)
    native = ctx.output_dir / "native"
    model = native / "model.sc"
    step = native / "model.step"
    results = native / "results.json"
    replay_log = native / "replay-log.json"

    run_document(
        document,
        save=model,
        export=step,
        results_out=results,
        replay_log_out=replay_log,
        work_dir=native / "replay_work",
    )
    return CheckOutcome.passed(
        artifacts=(model, step, results, replay_log),
    )


def geometry_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify the baseline 40 × 30 × 10 mm native box."""

    native = ctx.output_dir / "native"
    model = native / "model.sc"
    measurements = native / "measurements.json"

    run_command(
        [
            "solidcraft-cli",
            "eval",
            str(model),
            "--json-out",
            str(measurements),
        ]
    )
    data = load_json(measurements)

    require_equal("simple-box body count", data.get("body_count"), 1)
    require_equal(
        "simple-box baseline bounds",
        normalized_bounds(box_bounds(data)),
        {
            "min": [-20.0, -15.0, 0.0],
            "max": [20.0, 15.0, 10.0],
        },
    )
    require_equal(
        "simple-box baseline parameters",
        parameters(data),
        {
            "length": 40.0,
            "width": 30.0,
            "height": 10.0,
        },
    )

    timeline = data.get("timeline", [])
    timeline_state = [
        {
            "type": row.get("type"),
            "error": row.get("error"),
            "warning": row.get("warning"),
        }
        for row in timeline
    ]
    require_equal(
        "simple-box native timeline",
        timeline_state,
        [{
            "type": "BoxFeature",
            "error": None,
            "warning": None,
        }],
    )

    return CheckOutcome.passed(
        evidence={
            "body_count": 1,
            "bounds": normalized_bounds(box_bounds(data)),
            "parameters": parameters(data),
            "timeline": timeline_state,
        },
        artifacts=(measurements,),
    )




def visual_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify deterministic simple-box renders and expected-shape evidence."""

    native = ctx.output_dir / "native"
    visual = ctx.output_dir / "visual"
    report = verify_visual(
        model=native / "model.sc",
        measurements_path=native / "measurements.json",
        config_path=VISUAL_CONFIG,
        output_dir=visual,
    )

    if report["status"] != "pass":
        raise VerificationFailure(
            "simple-box visual verification",
            evidence=report,
        )

    artifacts = tuple(
        sorted(
            path
            for path in visual.rglob("*")
            if path.is_file()
        )
    )
    return CheckOutcome.passed(
        evidence=report,
        artifacts=artifacts,
    )


def saved_design_check(ctx: VerificationContext) -> CheckOutcome:
    """Change only the saved native length and prove the Box rebuilds."""

    native = ctx.output_dir / "native"
    model = native / "model.sc"
    mutated = native / "model-length-50.sc"
    measurements = native / "measurements-length-50.json"

    run_command(
        [
            "solidcraft-cli",
            "run",
            str(MUTATION),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--save",
            str(mutated),
        ]
    )
    run_command(
        [
            "solidcraft-cli",
            "eval",
            str(mutated),
            "--json-out",
            str(measurements),
        ]
    )
    data = load_json(measurements)

    require_equal("mutated simple-box body count", data.get("body_count"), 1)
    require_equal(
        "simple-box saved-design bounds",
        normalized_bounds(box_bounds(data)),
        {
            "min": [-25.0, -15.0, 0.0],
            "max": [25.0, 15.0, 10.0],
        },
    )
    require_equal(
        "simple-box saved-design parameters",
        parameters(data),
        {
            "length": 50.0,
            "width": 30.0,
            "height": 10.0,
        },
    )

    return CheckOutcome.passed(
        evidence={
            "bounds": normalized_bounds(box_bounds(data)),
            "parameters": parameters(data),
        },
        artifacts=(mutated, measurements),
    )


def main() -> int:
    """Run the explicit simple-box model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="simple-box",
        input_path=args.input.resolve(),
        output_dir=args.output.resolve(),
        work_dir=args.output.resolve() / "work",
        metadata={
            "section": labels["section"],
            "title": labels["title"],
        },
    )
    report = verify(
        context,
        (
            VerificationCheck("replay", replay_check),
            VerificationCheck("geometry", geometry_check),
            VerificationCheck("visual", visual_check),
            VerificationCheck("saved_design", saved_design_check),
        ),
    )
    print(
        "simple-box model verification: "
        + str(report["status"])
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
