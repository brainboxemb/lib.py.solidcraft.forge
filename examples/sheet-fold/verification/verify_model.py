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



INSPECTION = EXAMPLE / "verification" / "inspect_flat_pattern.json"


def geometry_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify formed sheet geometry and native feature history."""

    native = ctx.output_dir / "native"
    measurements = native / "measurements.json"
    data = evaluate(native / "model.sc", measurements)

    expected_bounds = [
        ([-40.0, -20.0, 0.0], [21.64380551, 20.0, 21.64380551]),
    ]
    require_equal("body count", data.get("body_count"), 1)
    require_true(
        "formed sheet bounds",
        bounds_match(data, expected_bounds, 0.01),
        expected=expected_bounds,
        actual=[body.get("bbox") for body in data.get("bodies", [])],
    )

    body = data["bodies"][0]
    require_true(
        "native sheet body",
        body.get("sheet_metal") is True and body.get("closed") is True,
        expected={"sheet_metal": True, "closed": True},
        actual={
            "sheet_metal": body.get("sheet_metal"),
            "closed": body.get("closed"),
        },
    )
    expected_volume = 80.0 * 40.0 * 2.0 - 3.141592653589793 * 3.0**2 * 2.0
    require_true(
        "sheet volume",
        close(body.get("volume_mm3", 0), expected_volume, 0.01),
        expected={"volume_mm3": expected_volume, "tolerance_mm3": 0.01},
        actual={"volume_mm3": body.get("volume_mm3")},
    )

    timeline = [
        (row.get("type"), row.get("name"))
        for row in data.get("timeline", [])
    ]
    require_equal(
        "native sheet timeline",
        timeline,
        [
            ("Sketch", "Blank"),
            ("BaseFlangeFeature", "BaseFlange1"),
            ("HoleFeature", "Hole1"),
            ("FoldFeature", "Fold1"),
        ],
    )

    blank = next(
        (
            row
            for row in data.get("sketches", [])
            if row.get("name") == "Blank"
        ),
        None,
    )
    require_true(
        "solved flat blank",
        blank is not None
        and blank.get("profiles") == 1
        and blank.get("curves") == 4
        and blank.get("status") == "solved",
        expected={"profiles": 1, "curves": 4, "status": "solved"},
        actual=blank,
    )

    return CheckOutcome.passed(
        evidence={
            "bounds": body.get("bbox"),
            "timeline": timeline,
            "blank": blank,
        },
        artifacts=(measurements,),
    )


def flat_pattern_check(ctx: VerificationContext) -> CheckOutcome:
    """Inspect the developed blank, cutout and bend rule."""

    native = ctx.output_dir / "native"
    target = native / "results-flat-pattern.json"
    rows = inspect_results(native / "model.sc", INSPECTION, target)

    require_true(
        "flat-pattern result count",
        isinstance(rows, list) and len(rows) == 1,
        expected=1,
        actual=len(rows) if isinstance(rows, list) else None,
    )
    flat = rows[0]

    size = flat.get("flat_size_mm")
    require_true(
        "flat blank size",
        isinstance(size, list)
        and len(size) == 3
        and vector_close(size, [80.0, 40.0, 2.0], 0.001),
        expected=[80.0, 40.0, 2.0],
        actual=size,
    )

    cutouts = flat.get("cutout_shapes", [])
    circle = (
        cutouts[0].get("circle")
        if len(cutouts) == 1 and isinstance(cutouts[0], dict)
        else None
    )
    require_true(
        "flat-pattern hole",
        isinstance(circle, dict)
        and vector_close(circle.get("center", []), [-20.0, 0.0], 0.001)
        and close(circle.get("radius", -1), 3.0, 0.001),
        expected={"center": [-20.0, 0.0], "radius": 3.0},
        actual=circle,
    )

    bends = flat.get("bends", [])
    bend = bends[0] if len(bends) == 1 else None
    require_true(
        "qualified bend",
        isinstance(bend, dict)
        and close(bend.get("angle_deg", 0), 90.0, 0.001)
        and close(bend.get("radius", 0), 2.0, 0.001)
        and close(bend.get("allowance", 0), 4.71238898038469, 0.001),
        expected={
            "angle_deg": 90.0,
            "radius": 2.0,
            "allowance": 4.71238898038469,
        },
        actual=bend,
    )
    require_true(
        "shared sheet rule",
        flat.get("rule") == "SheetFold Rule"
        and close(flat.get("thickness", 0), 2.0, 0.001)
        and close(flat.get("k_factor", 0), 0.5, 0.001),
        expected={"rule": "SheetFold Rule", "thickness": 2.0, "k_factor": 0.5},
        actual={
            "rule": flat.get("rule"),
            "thickness": flat.get("thickness"),
            "k_factor": flat.get("k_factor"),
        },
    )

    return CheckOutcome.passed(
        evidence={"flat_pattern": flat},
        artifacts=(target,),
    )


def main() -> int:
    """Run the explicit sheet-fold model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="sheet-fold",
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
            VerificationCheck("flat_pattern", flat_pattern_check),
        ),
    )
    print("sheet-fold model verification: " + str(report["status"]))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
