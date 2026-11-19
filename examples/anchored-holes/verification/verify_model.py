#!/usr/bin/env python3
"""Model-owned SolidCraft verification migrated from the historical qualification case."""

from __future__ import annotations

import argparse
import json
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


def bounds_match(data: dict[str, Any], expected, tolerance: float = 1e-3) -> bool:
    """Match body bounds without depending on SolidCraft body ordering."""

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
    """Evaluate one saved SolidCraft model and return its measurement object."""

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
    """Apply one saved-design mutation to a native model."""

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


def inspect_results(model: Path, command: Path, destination: Path) -> Any:
    """Run one read-only native inspection command and return its results."""

    run_command(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--results",
            "--json-out",
            str(destination),
        ]
    )
    return load_json(destination)



def geometry_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify plate geometry and native rectangular-pattern history."""

    native = ctx.output_dir / "native"
    measurements = native / "measurements.json"
    data = evaluate(native / "model.sc", measurements)

    expected_bounds = [([0, 0, 0], [100, 60, 10])]
    require_equal("body count", data.get("body_count"), 1)
    require_true(
        "plate bounds",
        bounds_match(data, expected_bounds),
        expected=expected_bounds,
        actual=[body.get("bbox") for body in data.get("bodies", [])],
    )

    body = data["bodies"][0]
    require_equal(
        "two cylindrical hole walls",
        body.get("face_types", {}).get("cylinder", 0),
        2,
    )
    expected_volume = 100.0 * 60.0 * 10.0 - 2.0 * 3.141592653589793 * 4.0**2 * 10.0
    require_true(
        "plate volume",
        close(body.get("volume_mm3", 0), expected_volume, 0.5),
        expected={"volume_mm3": expected_volume, "tolerance_mm3": 0.5},
        actual={"volume_mm3": body.get("volume_mm3")},
    )

    timeline = data.get("timeline", [])
    types = [row.get("type") for row in timeline]
    names = [row.get("name") for row in timeline]
    expected_types = [
        "Sketch",
        "ExtrudeFeature",
        "Sketch",
        "ExtrudeFeature",
        "RectangularPatternFeature",
    ]
    require_equal("native timeline types", types, expected_types)
    require_true(
        "native timeline names",
        len(names) == 5
        and names[0] == "Base"
        and names[2] == "Hole"
        and names[3] == "Hole"
        and names[4] == "RectangularPattern1",
        expected=["Base", None, "Hole", "Hole", "RectangularPattern1"],
        actual=names,
    )
    warnings = [
        (row.get("name"), row.get("warning"))
        for row in timeline
        if row.get("warning") is not None
    ]
    require_equal("native feature warnings", warnings, [])

    return CheckOutcome.passed(
        evidence={
            "bounds": body.get("bbox"),
            "cylindrical_faces": 2,
            "timeline_types": types,
            "timeline_names": names,
        },
        artifacts=(measurements,),
    )


def main() -> int:
    """Run the explicit anchored-holes model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="anchored-holes",
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
        ),
    )
    print("anchored-holes model verification: " + str(report["status"]))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
