#!/usr/bin/env python3
"""Normalize one or more completed Forge example outputs.

The result schema uses the checks Forge actually performs: integration,
native-model, geometry, saved-design and visual checks. Historical Q-number
labels are intentionally not part of this contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.cases import QUALIFICATION_CASES
from qualification.native_cases import mutation_spec


SCHEMA_VERSION = 5


def _read_json(path: Path) -> dict:
    """Read one JSON object, returning an empty object when it is absent."""

    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _stage_state(stages_root: Path, slug: str, stage: str) -> dict:
    """Return the unique state record for a named case-runner stage."""

    matches = tuple(sorted((stages_root / slug).glob(f"*-{stage}.json")))
    if len(matches) != 1:
        return {}
    return _read_json(matches[0])


def _stage_status(stages_root: Path, slug: str, stage: str) -> str:
    """Return pass/fail/missing for one required stage."""

    value = _stage_state(stages_root, slug, stage).get("status")
    return value if value in {"pass", "fail", "skipped"} else "missing"


def _existing_names(case_dir: Path, patterns: tuple[str, ...]) -> list[str]:
    """Return non-empty evidence files matching the requested patterns."""

    names: set[str] = set()
    for pattern in patterns:
        names.update(
            path.name
            for path in case_dir.glob(pattern)
            if path.is_file() and path.stat().st_size
        )
    return sorted(names)


def _command_count(output_root: Path, slug: str) -> int | None:
    """Return the number of generated SolidCraft commands for one case."""

    compiled = _read_json(output_root / f"{slug}.json")
    commands = compiled.get("commands")
    return len(commands) if isinstance(commands, list) else None


def _normal_status(value: object, *, default: str = "missing") -> str:
    """Normalize a consumer-owned status value."""

    text = str(value or default).lower()
    if text in {"pass", "fail", "review", "missing", "not-required", "blocked"}:
        return text
    return default


def _visual_status(visual: dict) -> tuple[str, str, str, list[str]]:
    """Return visual status plus its two explicit comparison checks."""

    status = _normal_status(visual.get("status"))
    regression = _normal_status(
        (visual.get("regression") or {}).get("status")
    )
    expected_shape = _normal_status(
        (visual.get("expected_shape") or {}).get("status")
    )
    required_views = list(
        (visual.get("expected_shape") or {}).get("required_views") or []
    )
    if status == "pass" and (
        regression != "pass" or expected_shape != "pass"
    ):
        status = "missing"
    return status, regression, expected_shape, required_views


def collect(
    output_root: Path,
    source_commit: str,
    forge_version: str,
    solidcraft_version: str,
    qualified_at: str,
    *,
    cases: tuple[str, ...] | None = None,
) -> dict:
    """Create semantic per-case results from already-produced item evidence."""

    output_root = Path(output_root)
    stages_root = output_root / "stages"
    native_root = output_root / "native"
    selected = (
        tuple(case["slug"] for case in QUALIFICATION_CASES)
        if cases is None
        else tuple(cases)
    )

    aggregate = {
        "schema_version": SCHEMA_VERSION,
        "source_commit": source_commit,
        "forge_version": forge_version,
        "solidcraft_version": solidcraft_version,
        "qualified_at": qualified_at,
        "cases": {},
    }

    selected_set = set(selected)
    for case in QUALIFICATION_CASES:
        slug = case["slug"]
        if slug not in selected_set:
            continue

        case_dir = native_root / slug
        case_dir.mkdir(parents=True, exist_ok=True)
        validation = _read_json(case_dir / "validation.json")
        visual = _read_json(case_dir / "visual-validation.json")

        compile_status = _stage_status(stages_root, slug, "compile")
        command_count = _command_count(output_root, slug)
        integration_status = (
            "pass"
            if compile_status == "pass" and command_count is not None
            else "fail"
            if compile_status == "fail"
            else "missing"
        )

        native_stage_statuses = {
            name: _stage_status(stages_root, slug, name)
            for name in ("replay", "evaluate", "gate")
        }
        if all(value == "pass" for value in native_stage_statuses.values()):
            native_status = "pass"
        elif "fail" in native_stage_statuses.values():
            native_status = "fail"
        else:
            native_status = "missing"

        geometry_status = _normal_status(validation.get("geometry"))
        saved_required = mutation_spec(slug) is not None
        saved_status = (
            _normal_status(validation.get("saved_design"))
            if saved_required
            else "not-required"
        )
        visual_status, regression, expected_shape, required_views = (
            _visual_status(visual)
        )

        images = _existing_names(case_dir, ("*.png",))
        images.sort(key=lambda name: (name != "model.png", name))
        native_files = _existing_names(
            case_dir,
            (
                "results*.json",
                "measurements*.json",
                "change-*.json",
                "parameters*.json",
                "joint-*.json",
                "model.json",
                "model*.sc",
                "model*.step",
                "export-*.json",
                "validation.json",
                "visual-validation.json",
                "visual-diff-*.png",
                "camera-*.json",
            ),
        )

        checks = {
            "integration": {
                "status": integration_status,
                "commands": command_count,
            },
            "native_model": {
                "status": native_status,
                "stages": native_stage_statuses,
                "evidence": [
                    name
                    for name in native_files
                    if name in {"results.json", "model.sc", "model.step"}
                ],
            },
            "geometry": {
                "status": geometry_status,
                "evidence": [
                    name
                    for name in native_files
                    if name.startswith("measurements")
                    or name.startswith("joint-")
                    or name == "results-bom.json"
                    or name == "validation.json"
                ],
            },
            "saved_design": {
                "status": saved_status,
                "required": saved_required,
                "reason": case["mutation"],
                "mutation": (
                    mutation_spec(slug)["label"]
                    if saved_required
                    else None
                ),
                "evidence": (
                    [
                        name
                        for name in native_files
                        if name in {
                            mutation_spec(slug)["save"],
                            mutation_spec(slug)["measurements"],
                        }
                    ]
                    if saved_required
                    else []
                ),
            },
            "visual": {
                "status": visual_status,
                "regression_status": regression,
                "expected_shape_status": expected_shape,
                "required_views": required_views,
                "images": images,
                "evidence": [
                    name
                    for name in native_files
                    if name == "visual-validation.json"
                    or name.startswith("visual-diff-")
                    or name.startswith("goal-")
                    or name.startswith("overlay-")
                ],
            },
        }

        blocked_reason = case.get("blocked_reason")
        if blocked_reason:
            for name, check in checks.items():
                if name != "integration":
                    check["status"] = "blocked"

        required = [
            checks["integration"]["status"],
            checks["native_model"]["status"],
            checks["geometry"]["status"],
            checks["visual"]["status"],
        ]
        if saved_required:
            required.append(checks["saved_design"]["status"])

        if blocked_reason:
            overall = "blocked"
        elif "fail" in required:
            overall = "fail"
        elif "missing" in required:
            overall = "incomplete"
        elif "review" in required:
            overall = "review"
        else:
            overall = "pass"

        result = {
            "schema_version": SCHEMA_VERSION,
            "case": slug,
            "title": case["title"],
            "source_commit": source_commit,
            "forge_version": forge_version,
            "solidcraft_version": solidcraft_version,
            "qualified_at": qualified_at,
            "status": overall,
            "blocked_reason": blocked_reason,
            "checks": checks,
            "evidence": {
                "native_files": native_files,
                "images": images,
            },
        }
        aggregate["cases"][slug] = result
        (case_dir / "qualification-result.json").write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )

    qualification_dir = output_root / "qualification"
    qualification_dir.mkdir(parents=True, exist_ok=True)
    (qualification_dir / "results.json").write_text(
        json.dumps(aggregate, indent=2) + "\n",
        encoding="utf-8",
    )
    return aggregate


def main() -> int:
    """Normalize staged output supplied by the Forge pipeline."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--forge-version", required=True)
    parser.add_argument("--solidcraft-version", required=True)
    parser.add_argument("--qualified-at", required=True)
    parser.add_argument("--cases", default="")
    args = parser.parse_args()
    cases = tuple(
        value.strip()
        for value in args.cases.replace(" ", ",").split(",")
        if value.strip()
    ) or None
    collect(
        args.output_root,
        args.source_sha,
        args.forge_version,
        args.solidcraft_version,
        args.qualified_at,
        cases=cases,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
