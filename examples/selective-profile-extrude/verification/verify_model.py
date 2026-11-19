#!/usr/bin/env python3
"""Model-owned SolidCraft verification migrated from the historical qualification case."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml

from cad_verification import (
    BodyEnvelope,
    compare_scalar,
    match_body_envelopes,
    CheckOutcome,
    VerificationCheck,
    VerificationContext,
    VerificationFailure,
    run_command,
    verify,
)
from scpf.headless import run_document
from verification.solidcraft_measurements import measured_body_envelopes


EXAMPLE = Path(__file__).resolve().parents[1]
MODEL_METADATA = EXAMPLE / "model.yml"
MODEL_FIELDS = {
    "section",
    "title",
    "tagline",
    "description",
    "parameters",
    "stages",
}


def model_metadata() -> dict[str, Any]:
    """Load generic presentation metadata and reject accidental extra schema."""

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


def load_json(path: Path) -> Any:
    """Read JSON evidence produced by SolidCraft."""

    return json.loads(path.read_text(encoding="utf-8"))


def parameters(data: dict[str, Any]) -> dict[str, float]:
    """Return native parameter values keyed by parameter name."""

    return {
        str(row["name"]): float(row["value"])
        for row in data.get("params", [])
    }


def body_size(body: dict[str, Any]) -> tuple[float, float, float]:
    """Return one body's XYZ size."""

    return tuple(
        round(float(hi) - float(lo), 6)
        for lo, hi in zip(body["bbox"]["min"], body["bbox"]["max"])
    )


def bodies_named(data: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    """Return bodies whose native name starts with the requested prefix."""

    return [
        body
        for body in data.get("bodies", [])
        if str(body.get("name", "")).startswith(prefix)
    ]


def one_body(data: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Return exactly one body with the requested native-name prefix."""

    rows = bodies_named(data, prefix)
    require_equal(f"{prefix} body count", len(rows), 1)
    return rows[0]


def require_equal(label: str, actual: Any, expected: Any) -> None:
    """Raise a model-level verification failure for one mismatch."""

    if actual != expected:
        raise VerificationFailure(
            label,
            evidence={"expected": expected, "actual": actual},
        )


def require_true(label: str, condition: bool, *, expected: Any, actual: Any) -> None:
    """Raise a model-level verification failure for one predicate."""

    if not condition:
        raise VerificationFailure(
            label,
            evidence={"expected": expected, "actual": actual},
        )


def replay_check(ctx: VerificationContext) -> CheckOutcome:
    """Replay the Forge command document into an editable native design."""

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


def evaluate(model: Path, destination: Path) -> dict[str, Any]:
    """Evaluate one saved SolidCraft model and return its measurements."""

    run_command(
        [
            "solidcraft-cli",
            "eval",
            str(model),
            "--json-out",
            str(destination),
        ]
    )
    value = load_json(destination)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {destination}")
    return value


def mutate(model: Path, command: Path, destination: Path) -> None:
    """Apply one saved-design parameter mutation."""

    run_command(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--save",
            str(destination),
        ]
    )


def geometry_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify the historical selective-profile-extrude native model contract."""

    native = ctx.output_dir / "native"
    measurements = native / "measurements.json"
    data = evaluate(native / "model.sc", measurements)
    expected_bounds = [[[-60,-30,0],[60,30,5]]]
    match_body_envelopes(
        tuple(
            BodyEnvelope(
                tuple(minimum),
                tuple(maximum),
                f"baseline bounds {index + 1}",
            )
            for index, (minimum, maximum) in enumerate(expected_bounds)
        ),
        measured_body_envelopes(data),
        0.01,
    )

    require_equal("body count", data.get("body_count"), 1)
    expected_parameters = {"hole_diameter": 8.0, "hole_pitch": 20.0}
    actual_parameters = parameters(data)
    require_true(
        "baseline pattern parameters",
        all(actual_parameters.get(name) == value for name, value in expected_parameters.items()),
        expected=expected_parameters,
        actual={name: actual_parameters.get(name) for name in expected_parameters},
    )
    body = data["bodies"][0]
    expected_volume = 120.0 * 60.0 * 5.0 - 3.0 * math.pi * 4.0**2 * 5.0
    removed_volume = math.pi * 4.0**2 * 5.0
    expected_center_x = -(removed_volume * (-30.0 - 10.0 + 30.0)) / expected_volume
    compare_scalar(
        expected_volume,
        body["volume_mm3"],
        0.05,
        label="three selected profiles volume",
    )
    require_equal(
        "three selected profiles cylindrical faces",
        body.get("face_types", {}).get("cylinder"),
        3,
    )
    compare_scalar(
        expected_center_x,
        body["center_of_mass"][0],
        0.001,
        label="unselected profile remains filled",
    )
    sketches = {row.get("name"): row for row in data.get("sketches", [])}
    selected = sketches.get("Selected holes")
    require_true(
        "selected-hole sketch solved",
        selected is not None and selected.get("status") == "solved" and len(sketches) == 1,
        expected={"Selected holes": "solved"},
        actual={name: row.get("status") for name, row in sketches.items()},
    )
    timeline = [(row.get("type"), row.get("name")) for row in data.get("timeline", [])]
    require_equal(
        "selective extrusion history",
        timeline,
        [("BoxFeature", "Box1"), ("Sketch", "Selected holes"), ("ExtrudeFeature", "Selected holes")],
    )

    return CheckOutcome.passed(
        evidence={
            "body_count": data.get("body_count"),
            "bounds": [body.get("bbox") for body in data.get("bodies", [])],
        },
        artifacts=(measurements,),
    )

MUTATION = EXAMPLE / "verification" / "change_pattern.json"


def saved_design_check(ctx: VerificationContext) -> CheckOutcome:
    """Apply the historical saved-design mutation and verify the rebuild."""

    native = ctx.output_dir / "native"
    mutated = native / "model-pattern-mutated.sc"
    measurements = native / "measurements-pattern-mutated.json"

    mutate(native / "model.sc", MUTATION, mutated)
    data = evaluate(mutated, measurements)
    expected_bounds = [[[-60,-30,0],[60,30,5]]]
    match_body_envelopes(
        tuple(
            BodyEnvelope(
                tuple(minimum),
                tuple(maximum),
                f"mutated bounds {index + 1}",
            )
            for index, (minimum, maximum) in enumerate(expected_bounds)
        ),
        measured_body_envelopes(data),
        0.01,
    )

    expected_parameters = {"hole_diameter": 10.0, "hole_pitch": 24.0}
    actual_parameters = parameters(data)
    require_true(
        "mutated pattern parameters",
        all(actual_parameters.get(name) == value for name, value in expected_parameters.items()),
        expected=expected_parameters,
        actual={name: actual_parameters.get(name) for name in expected_parameters},
    )
    body = data["bodies"][0]
    expected_volume = 120.0 * 60.0 * 5.0 - 3.0 * math.pi * 5.0**2 * 5.0
    removed_volume = math.pi * 5.0**2 * 5.0
    expected_center_x = -(removed_volume * (-30.0 - 6.0 + 42.0)) / expected_volume
    compare_scalar(
        expected_volume,
        body["volume_mm3"],
        0.05,
        label="mutated selected profiles volume",
    )
    require_equal(
        "mutated selected profiles cylindrical faces",
        body.get("face_types", {}).get("cylinder"),
        3,
    )
    compare_scalar(
        expected_center_x,
        body["center_of_mass"][0],
        0.001,
        label="profile selection follows moved pattern",
    )
    sketches = {row.get("name"): row for row in data.get("sketches", [])}
    selected = sketches.get("Selected holes")
    require_true(
        "mutated sketch remains solved",
        selected is not None and selected.get("status") == "solved" and len(sketches) == 1,
        expected={"Selected holes": "solved"},
        actual={name: row.get("status") for name, row in sketches.items()},
    )
    timeline = [(row.get("type"), row.get("name")) for row in data.get("timeline", [])]
    require_equal(
        "mutated selective history",
        timeline,
        [("BoxFeature", "Box1"), ("Sketch", "Selected holes"), ("ExtrudeFeature", "Selected holes")],
    )

    return CheckOutcome.passed(
        evidence={
            "parameters": parameters(data),
            "bounds": [body.get("bbox") for body in data.get("bodies", [])],
        },
        artifacts=(mutated, measurements),
    )

def main() -> int:
    """Run the explicit selective-profile-extrude model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="selective-profile-extrude",
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
            VerificationCheck("saved_design", saved_design_check),
        ),
    )
    print("selective-profile-extrude model verification: " + str(report["status"]))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
