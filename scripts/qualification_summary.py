#!/usr/bin/env python3
"""Compose existing Forge qualification semantics from resolved evidence.

This adapter does not execute Forge, SolidCraft, reference CAD or image
comparison. It maps already-produced evidence back to the schema-5
qualification meaning used by the public Pages site.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REFERENCE_IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")
PUBLIC_CHECKS = ("integration", "native_model", "geometry", "saved_design", "visual")
SCHEMA_VERSION = 5


def _semantic_api():
    """Load released generic semantic composition only when composition runs."""

    from cad_verification import (
        SemanticCheck,
        compose_item_results,
        compose_semantic_result,
        semantic_checks_from_report,
    )

    return (
        SemanticCheck,
        compose_item_results,
        compose_semantic_result,
        semantic_checks_from_report,
    )


def _read_object(path: Path) -> dict[str, Any] | None:
    """Read one JSON object, returning None for absent/non-object evidence."""

    path = Path(path)
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def _check_status(value: Any, *, default: str = "missing") -> str:
    """Map evidence status text to the generic semantic-check vocabulary."""

    text = str(value or "").lower()
    if text in {
        "pass",
        "fail",
        "error",
        "missing",
        "review",
        "blocked",
        "not-required",
        "skipped",
    }:
        return text
    if text == "incomplete":
        return "missing"
    return default


def _public_status(value: str) -> str:
    """Map a generic composed result back to the public case status vocabulary."""

    return "incomplete" if value == "incomplete" else value


def _composed_check_status(name: str, statuses: list[str]) -> str:
    """Compose several evidence statuses into one public check status."""

    if not statuses:
        return "missing"
    SemanticCheck, _, compose_semantic_result, _ = _semantic_api()
    result = compose_semantic_result(
        SemanticCheck(f"{name}_{index}", _check_status(status))
        for index, status in enumerate(statuses)
    )
    return "missing" if result["status"] == "incomplete" else result["status"]


def _command_count(case_root: Path) -> int | None:
    document = _read_object(case_root / "solidcraft.json")
    commands = document.get("commands") if document else None
    if not isinstance(commands, list) or not commands:
        return None
    return len(commands)


def _integration_check(case_root: Path) -> dict[str, Any]:
    step = _read_object(case_root / ".cad-ci" / "steps" / "contract_test.json")
    count = _command_count(case_root)
    status = _check_status(step.get("status") if step else None)
    if status == "pass" and count is None:
        status = "missing"
    return {"status": status, "commands": count}


def _native_check(case_root: Path) -> dict[str, Any]:
    step = _read_object(case_root / ".cad-ci" / "steps" / "model_verify.json")
    native = case_root / "model_verify" / "native"
    names = ("model.sc", "model.step", "results.json")
    present = [name for name in names if _nonempty(native / name)]

    if len(present) == len(names):
        status = "pass"
    else:
        status = _check_status(step.get("status") if step else None)
        if status == "pass":
            status = "missing"

    return {"status": status, "evidence": present}


def _verification_checks(case_root: Path):
    report = _read_object(case_root / "model_verify" / "verification.json")
    if report is None:
        return ()
    _, _, _, semantic_checks_from_report = _semantic_api()
    return semantic_checks_from_report(report)


def _geometry_check(case_root: Path) -> dict[str, Any]:
    matches = [check for check in _verification_checks(case_root) if check.name == "baseline"]
    if len(matches) != 1:
        return {"status": "missing", "evidence": []}
    row = matches[0]
    evidence = ["model_verify/verification.json"]
    for artifact in (row.evidence or {}).get("artifacts", []):
        path = artifact.get("path") if isinstance(artifact, dict) else None
        if isinstance(path, str):
            evidence.append(f"model_verify/{path}")
    return {"status": _check_status(row.status), "evidence": evidence}


def _saved_design_check(case_root: Path) -> dict[str, Any]:
    checks = [
        check
        for check in _verification_checks(case_root)
        if check.name.startswith("saved_design_")
    ]
    if not checks:
        return {
            "status": "not-required",
            "required": False,
            "evidence": [],
        }

    SemanticCheck, _, compose_semantic_result, _ = _semantic_api()
    result = compose_semantic_result(
        SemanticCheck(
            check.name,
            _check_status(check.status),
            required=True,
            reason=check.reason,
            evidence=check.evidence,
        )
        for check in checks
    )
    evidence = ["model_verify/verification.json"]
    for check in checks:
        for artifact in (check.evidence or {}).get("artifacts", []):
            path = artifact.get("path") if isinstance(artifact, dict) else None
            if isinstance(path, str):
                evidence.append(f"model_verify/{path}")

    return {
        "status": "missing" if result["status"] == "incomplete" else result["status"],
        "required": True,
        "evidence": sorted(set(evidence)),
    }


def _visual_check(case_root: Path) -> dict[str, Any]:
    report = _read_object(case_root / "model_verify" / "visual.json")
    if report is None:
        return {
            "status": "missing",
            "regression_status": "missing",
            "expected_shape_status": "missing",
            "required_views": [],
            "images": [],
            "evidence": [],
        }

    semantic = report.get("semantic")
    status = _check_status((semantic or {}).get("status"))
    if status == "missing":
        status = _check_status(report.get("status"))

    views = report.get("views")
    rows = views if isinstance(views, list) else []
    regression = []
    expected = []
    required_views = []
    images = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        view = row.get("view")
        if isinstance(view, str):
            required_views.append(view)
        evidence = row.get("evidence")
        if not isinstance(evidence, dict):
            continue
        regression.append(_check_status(evidence.get("baseline_status")))
        expected.append(_check_status(evidence.get("expected_shape_status")))
        for key in ("actual_image", "diff_image", "goal_image", "overlay_image"):
            path = evidence.get(key)
            if isinstance(path, str):
                images.append(path)

    return {
        "status": status,
        "regression_status": _composed_check_status("regression", regression),
        "expected_shape_status": _composed_check_status("expected_shape", expected),
        "required_views": required_views,
        "images": sorted(set(images)),
        "evidence": ["model_verify/visual.json"],
    }


def _reference_check(evidence_root: Path, slug: str):
    """Return the internal reference gate without adding a public status row."""

    SemanticCheck, _, compose_semantic_result, _ = _semantic_api()
    matches = list(
        Path(evidence_root).glob(f"**/references/{slug}/*/verification.json")
    )
    by_name: dict[str, tuple[Path, dict[str, Any]]] = {}
    duplicate = False
    for path in matches:
        report = _read_object(path)
        implementation = report.get("implementation") if report else None
        if implementation not in REFERENCE_IMPLEMENTATIONS:
            continue
        if implementation in by_name:
            duplicate = True
        else:
            by_name[implementation] = (path, report)

    checks = []
    evidence = []
    for implementation in REFERENCE_IMPLEMENTATIONS:
        row = by_name.get(implementation)
        status = _check_status(row[1].get("status") if row else None)
        path = row[0].relative_to(evidence_root).as_posix() if row else None
        checks.append(
            SemanticCheck(
                implementation,
                status,
                evidence={"path": path} if path else None,
            )
        )
        if path:
            evidence.append(path)

    if duplicate:
        checks.append(SemanticCheck("duplicate_reference", "error"))

    return compose_semantic_result(checks), evidence


def compose_case(evidence_root: Path, slug: str):
    """Compose one public qualification result and one internal publication gate."""

    evidence_root = Path(evidence_root)
    case_root = evidence_root / "examples" / slug

    checks = {
        "integration": _integration_check(case_root),
        "native_model": _native_check(case_root),
        "geometry": _geometry_check(case_root),
        "saved_design": _saved_design_check(case_root),
        "visual": _visual_check(case_root),
    }

    SemanticCheck, _, compose_semantic_result, _ = _semantic_api()
    visible_semantic = compose_semantic_result(
        SemanticCheck(
            name,
            _check_status(checks[name]["status"]),
            required=(name != "saved_design" or checks[name]["required"]),
            evidence=checks[name],
        )
        for name in PUBLIC_CHECKS
    )
    reference_semantic, reference_evidence = _reference_check(evidence_root, slug)
    publication_semantic = compose_semantic_result(
        (
            SemanticCheck(
                "qualification",
                _check_status(visible_semantic["status"]),
                evidence=visible_semantic,
            ),
            SemanticCheck(
                "reference",
                _check_status(reference_semantic["status"]),
                evidence={"files": reference_evidence},
            ),
        )
    )

    public_result = {
        "schema_version": SCHEMA_VERSION,
        "case": slug,
        "status": _public_status(visible_semantic["status"]),
        "blocked_reason": None,
        "checks": checks,
        "evidence": {
            "native_files": sorted(
                set(
                    checks["native_model"]["evidence"]
                    + checks["geometry"]["evidence"]
                    + checks["saved_design"]["evidence"]
                    + checks["visual"]["evidence"]
                )
            ),
            "images": checks["visual"]["images"],
        },
    }
    return public_result, publication_semantic


def compose_cases(evidence_root: Path, slugs: tuple[str, ...]):
    """Compose ordered case results and the internal all-case publication gate."""

    _, compose_item_results, _, _ = _semantic_api()
    cases = {}
    gates = []
    for slug in slugs:
        result, gate = compose_case(evidence_root, slug)
        cases[slug] = result
        gates.append((slug, gate))
    return {
        "schema_version": SCHEMA_VERSION,
        "cases": cases,
    }, compose_item_results(gates)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--case", action="append", dest="cases", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result, gate = compose_cases(args.evidence_root, tuple(args.cases))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"qualification summary: {gate['status']}")
    return 0 if gate["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
