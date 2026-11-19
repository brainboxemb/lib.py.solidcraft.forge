#!/usr/bin/env python3
"""Model-owned SolidCraft verification migrated from the historical qualification case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from cad_verification import (
    BodyEnvelope,
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



INSPECTION = EXAMPLE / "verification" / "inspect_bom.json"


def geometry_check(ctx: VerificationContext) -> CheckOutcome:
    """Verify the three visible native bodies."""

    native = ctx.output_dir / "native"
    measurements = native / "measurements.json"
    data = evaluate(native / "model.sc", measurements)

    expected_bounds = [
        ([-5, -1, 0], [5, 1, 20]),
        ([6, -1, 0], [16, 1, 20]),
        ([-17.5, 15, 0], [17.5, 25, 40]),
    ]
    require_equal("body count", data.get("body_count"), 3)
    match_body_envelopes(
        tuple(
            BodyEnvelope(
                tuple(minimum),
                tuple(maximum),
                f"grouped model bounds {index + 1}",
            )
            for index, (minimum, maximum) in enumerate(expected_bounds)
        ),
        measured_body_envelopes(data),
        1e-3,
    )

    return CheckOutcome.passed(
        evidence={"bounds": [body.get("bbox") for body in data.get("bodies", [])]},
        artifacts=(measurements,),
    )


def hierarchy_check(ctx: VerificationContext) -> CheckOutcome:
    """Inspect BOM levels and component occurrence grounding."""

    native = ctx.output_dir / "native"
    target = native / "results-bom.json"
    inspection = inspect_results(native / "model.sc", INSPECTION, target)

    require_true(
        "inspection result count",
        isinstance(inspection, list) and len(inspection) == 3,
        expected=3,
        actual=len(inspection) if isinstance(inspection, list) else None,
    )
    top, flat, component_list = inspection

    top_rows = {
        row["definition"]: row["count"]
        for row in top.get("rows", [])
    }
    require_true(
        "top BOM",
        top.get("levels") == "top"
        and top_rows == {"Frame": 1, "PanelGroup": 1}
        and top.get("total_occurrences") == 2,
        expected={"Frame": 1, "PanelGroup": 1, "total_occurrences": 2},
        actual={**top_rows, "total_occurrences": top.get("total_occurrences")},
    )

    flat_rows = {
        row["definition"]: row["count"]
        for row in flat.get("rows", [])
    }
    require_true(
        "flat BOM",
        flat.get("levels") == "flat"
        and flat_rows == {"Frame": 1, "Panel": 2}
        and flat.get("total_occurrences") == 3,
        expected={"Frame": 1, "Panel": 2, "total_occurrences": 3},
        actual={**flat_rows, "total_occurrences": flat.get("total_occurrences")},
    )

    components = {
        component["name"]: component
        for component in component_list.get("components", [])
    }
    group_occurrences = components.get("PanelGroup", {}).get("occurrences", [])
    panel_occurrences = components.get("Panel", {}).get("occurrences", [])
    require_true(
        "PanelGroup grounding",
        len(group_occurrences) == 1
        and group_occurrences[0].get("grounded") is False,
        expected={"count": 1, "grounded": False},
        actual={
            "count": len(group_occurrences),
            "grounded": (
                group_occurrences[0].get("grounded")
                if group_occurrences else None
            ),
        },
    )
    require_true(
        "Panel occurrence grounding",
        len(panel_occurrences) == 2
        and panel_occurrences[0].get("grounded") is True,
        expected={"count": 2, "first_grounded": True},
        actual={
            "count": len(panel_occurrences),
            "first_grounded": (
                panel_occurrences[0].get("grounded")
                if panel_occurrences else None
            ),
        },
    )

    return CheckOutcome.passed(
        evidence={
            "top_bom": top_rows,
            "flat_bom": flat_rows,
            "panel_group_occurrences": len(group_occurrences),
            "panel_occurrences": len(panel_occurrences),
        },
        artifacts=(target,),
    )


def main() -> int:
    """Run the explicit group-hierarchy model verification checks."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    labels = model_metadata()
    context = VerificationContext(
        verification_id="group-hierarchy",
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
            VerificationCheck("hierarchy", hierarchy_check),
        ),
    )
    print("group-hierarchy model verification: " + str(report["status"]))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
