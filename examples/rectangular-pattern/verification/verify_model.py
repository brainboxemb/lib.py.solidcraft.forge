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
    CheckOutcome,
    VerificationCheck,
    VerificationContext,
    VerificationFailure,
    run_command,
    verify,
)
from scpf.headless import run_document


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


def close(actual: float, expected: float, tolerance: float = 1e-3) -> bool:
    """Return whether two engineering values match within tolerance."""

    return abs(float(actual) - float(expected)) <= tolerance


def vector_close(actual, expected, tolerance: float = 1e-3) -> bool:
    """Compare equally-sized numeric vectors."""

    return (
        len(actual) == len(expected)
        and all(close(a, b, tolerance) for a, b in zip(actual, expected))
    )


def bbox_close(body: dict[str, Any], minimum, maximum, tolerance: float = 1e-3) -> bool:
    """Compare one body's axis-aligned bounds."""

    return (
        vector_close(body["bbox"]["min"], minimum, tolerance)
        and vector_close(body["bbox"]["max"], maximum, tolerance)
    )


def bounds_match(data: dict[str, Any], expected, tolerance: float = 1e-3) -> bool:
    """Match body bounds without depending on native body ordering."""

    actual = [
        (body["bbox"]["min"], body["bbox"]["max"])
        for body in data.get("bodies", [])
        if isinstance(body.get("bbox"), dict)
    ]
    if len(actual) != len(expected):
        return False
    remaining = list(actual)
    for minimum, maximum in expected:
        hit = next(
            (
                index
                for index, (lo, hi) in enumerate(remaining)
                if vector_close(lo, minimum, tolerance)
                and vector_close(hi, maximum, tolerance)
            ),
            None,
        )
        if hit is None:
            return False
        remaining.pop(hit)
    return not remaining


def require_bounds(label: str, data: dict[str, Any], expected, tolerance: float = 1e-3) -> None:
    """Require the declared model bounds."""

    require_true(
        label,
        bounds_match(data, expected, tolerance),
        expected=expected,
        actual=[
            (body["bbox"]["min"], body["bbox"]["max"])
            for body in data.get("bodies", [])
        ],
    )


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
    """Verify the historical rectangular-pattern native model contract."""

    native = ctx.output_dir / "native"
    measurements = native / "measurements.json"
    data = evaluate(native / "model.sc", measurements)
    expected_bounds = [[[-60,-40,0],[60,40,4]]]
    require_bounds("baseline bounds", data, expected_bounds, 0.01)

    require_equal("body count", data.get("body_count"), 1)
    body = data["bodies"][0]
    expected_volume = 120.0 * 80.0 * 4.0 - 6.0 * (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
    faces = body.get("face_types", {})
    require_true(
        "3 x 2 Slot pattern geometry",
        close(body["volume_mm3"], expected_volume, 0.01)
        and body.get("faces") == 30
        and faces.get("cylinder") == 12
        and faces.get("plane") == 18,
        expected={"volume_mm3": expected_volume, "faces": 30, "cylinder": 12, "plane": 18},
        actual={"volume_mm3": body["volume_mm3"], "faces": body.get("faces"), "face_types": faces},
    )
    sketch = next((row for row in data.get("sketches", []) if row.get("name") == "Slot"), None)
    require_true(
        "source Slot sketch",
        sketch is not None
        and sketch.get("curves") == 5
        and sketch.get("profiles") == 1
        and sketch.get("status") == "solved",
        expected={"curves": 5, "profiles": 1, "status": "solved"},
        actual=sketch,
    )
    timeline = [(row.get("type"), row.get("name")) for row in data.get("timeline", [])]
    require_equal(
        "rectangular feature history",
        timeline,
        [
            ("BoxFeature", "Box1"),
            ("Sketch", "Slot"),
            ("ExtrudeFeature", "Slot"),
            ("RectangularPatternFeature", "RectangularPattern1"),
        ],
    )

    return CheckOutcome.passed(
        evidence={
            "body_count": data.get("body_count"),
            "bounds": [body.get("bbox") for body in data.get("bodies", [])],
        },
        artifacts=(measurements,),
    )

MUTATION = EXAMPLE / "verification" / "change_columns_pitch.json"


def saved_design_check(ctx: VerificationContext) -> CheckOutcome:
    """Apply the historical saved-design mutation and verify the rebuild."""

    native = ctx.output_dir / "native"
    mutated = native / "model-columns-2-pitch-30.sc"
    measurements = native / "measurements-columns-2-pitch-30.json"

    mutate(native / "model.sc", MUTATION, mutated)
    data = evaluate(mutated, measurements)
    expected_bounds = [[[-60,-40,0],[60,40,4]]]
    require_bounds("mutated bounds", data, expected_bounds, 0.01)

    expected_parameters = {"columns": 2.0, "pitch": 30.0, "rows": 2.0, "row_pitch": 28.0}
    require_equal("mutated pattern parameters", parameters(data), expected_parameters)
    require_equal("mutated body count", data.get("body_count"), 1)
    body = data["bodies"][0]
    slot_volume = (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
    expected_volume = 120.0 * 80.0 * 4.0 - 4.0 * slot_volume
    expected_center = [
        -(4.0 * slot_volume * 15.0) / expected_volume,
        -(4.0 * slot_volume * 14.0) / expected_volume,
        2.0,
    ]
    faces = body.get("face_types", {})
    require_true(
        "2 x 2 rebuilt Slot pattern",
        close(body["volume_mm3"], expected_volume, 0.01)
        and body.get("faces") == 22
        and faces.get("cylinder") == 8
        and faces.get("plane") == 14,
        expected={"volume_mm3": expected_volume, "faces": 22, "cylinder": 8, "plane": 14},
        actual={"volume_mm3": body["volume_mm3"], "faces": body.get("faces"), "face_types": faces},
    )
    require_true(
        "mutated Slot layout center",
        vector_close(body["center_of_mass"], expected_center, 0.001),
        expected=expected_center,
        actual=body["center_of_mass"],
    )
    sketch = next((row for row in data.get("sketches", []) if row.get("name") == "Slot"), None)
    require_true(
        "mutated source Slot sketch",
        sketch is not None
        and sketch.get("curves") == 5
        and sketch.get("profiles") == 1
        and sketch.get("status") == "solved",
        expected={"curves": 5, "profiles": 1, "status": "solved"},
        actual=sketch,
    )
    timeline = [(row.get("type"), row.get("name")) for row in data.get("timeline", [])]
    require_equal(
        "mutated rectangular history",
        timeline,
        [
            ("BoxFeature", "Box1"),
            ("Sketch", "Slot"),
            ("ExtrudeFeature", "Slot"),
            ("RectangularPatternFeature", "RectangularPattern1"),
        ],
    )

    return CheckOutcome.passed(
        evidence={
            "parameters": parameters(data),
            "bounds": [body.get("bbox") for body in data.get("bodies", [])],
        },
        artifacts=(mutated, measurements),
    )

def main() -> int:
    """Run the explicit rectangular-pattern model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="rectangular-pattern",
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
    print("rectangular-pattern model verification: " + str(report["status"]))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
