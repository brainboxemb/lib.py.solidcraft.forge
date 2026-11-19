#!/usr/bin/env python3
"""Plan one Forge Actions run from event metadata and changed paths.

The planner returns concrete Forge work: a target verification stage, selected
example cases and optional shared evidence checks. It does not invent a second
"gate" vocabulary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.impact import affected_cases, changed_paths, classify, target_stage
from qualification.preview_scope import reference_smoke_reasons


WEEKLY_FULL_CRON = "17 3 * * 1"
RECONCILE_CRON = "41 4 * * *"
FORGE_TRIGGER = ".github/workflows/forge.trigger"

PIPELINE_PATHS = frozenset(
    {
        ".github/workflows/forge.yml",
        ".github/workflows/preflight.yml",
        ".github/workflows/preview.yml",
        ".github/workflows/qualification-image.yml",
        ".github/workflows/qualification-smoke.yml",
        ".github/workflows/qualify-main.yml",
        ".github/workflows/reconcile.yml",
        ".github/workflows/release.yml",
        ".github/workflows/scpf-affected.yml",
        ".github/workflows/scpf.yml",
        ".github/workflows/site.yml",
        ".github/workflows/solidcraft-contracts.yml",
        "scripts/ci_preflight.py",
        "scripts/forge_pipeline.py",
        "scripts/forge_scope.py",
        "scripts/qualification_image.py",
        "cad-ci.yml",
        "scripts/qualification_evidence_ci.py",
        "qualification/item_gate.py",
        "qualification/reference_suite/ci.yml",
        "qualification/diagrams/ci.yml",
        "qualification/tool_qualification/ci.yml",
        "qualification/tests/test_item_gate.py",
        "qualification/tests/test_tool_cad_ci_migration.py",
        "scripts/release/publish_release.py",
        "qualification/tests/test_forge_pipeline.py",
        "qualification/tests/test_forge_scope.py",
        "qualification/tests/test_generated_output.py",
        "site/tests/test_publishing.py",
        "site/tests/test_qualification_image.py",
    }
)

CONTRACT_FILES = frozenset({"scripts/solidcraft_snapshot.py"})
CONTRACT_PREFIXES = ("docs/vendor/solidcraft/",)


def _norm(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def contract_snapshot_required(paths: tuple[str, ...] | list[str]) -> bool:
    """Return whether the pinned SolidCraft command snapshot must be checked."""

    for raw in paths:
        path = _norm(raw)
        if path in CONTRACT_FILES:
            return True
        if path.startswith(CONTRACT_PREFIXES):
            return True
        if path.startswith("scpf/scpf/") and path.endswith(".py"):
            return True
    return False


def pipeline_only(paths: tuple[str, ...] | list[str]) -> bool:
    """Return whether changes affect only CI orchestration/presentation."""

    normalized = tuple(_norm(path) for path in paths)
    if not normalized:
        return False

    has_pipeline_change = False
    for path in normalized:
        if path in PIPELINE_PATHS:
            has_pipeline_change = True
            continue
        if classify((path,)) in {"presentation", "publication"}:
            continue
        return False
    return has_pipeline_change


def empty_plan(operation: str) -> dict:
    """Return a no-technical-work plan for cleanup/reconcile operations."""

    return {
        "operation": operation,
        "risk": "presentation",
        "stage": "none",
        "cases": "",
        "verify_references": False,
        "verify_diagrams": False,
        "verify_pipeline": False,
        "verify_contracts": False,
        "needs_image": False,
        "site_only": False,
        "release": False,
    }


def make_plan(
    *,
    event_name: str,
    event_action: str = "",
    base: str = "",
    head: str = "",
    ref_name: str = "",
    schedule: str = "",
    paths: tuple[str, ...] | list[str] | None = None,
) -> dict:
    """Return the concrete Forge work required for one workflow event."""

    if event_name == "pull_request" and event_action == "closed":
        return empty_plan("cleanup")

    if event_name == "schedule" and schedule == RECONCILE_CRON:
        return empty_plan("reconcile")

    if event_name == "workflow_dispatch" and ref_name != "main":
        raise ValueError("manual Forge qualification is only allowed on main")

    if event_name == "workflow_dispatch" or (
        event_name == "schedule" and schedule == WEEKLY_FULL_CRON
    ):
        return {
            "operation": "main",
            "risk": "foundational",
            "stage": "tool_qualification",
            "cases": "",
            "verify_references": True,
            "verify_diagrams": True,
            "verify_pipeline": False,
            "verify_contracts": False,
            "needs_image": True,
            "site_only": False,
            "release": False,
        }

    if event_name not in {"pull_request", "push"}:
        raise ValueError(f"unsupported Forge event: {event_name}")

    if paths is None:
        if not (base and head):
            raise ValueError(f"{event_name} planning requires base and head")
        selected_paths = changed_paths(base, head)
    else:
        selected_paths = tuple(_norm(path) for path in paths)

    verify_contracts = contract_snapshot_required(selected_paths)
    verify_pipeline = pipeline_only(selected_paths)

    if event_name == "push" and FORGE_TRIGGER in selected_paths:
        cases = ()
        risk = "foundational"
        stage = "tool_qualification"
        verify_references = True
        verify_diagrams = True
        verify_pipeline = False
    elif verify_pipeline:
        cases = ()
        risk = "publication"
        stage = "none"
        verify_references = False
        verify_diagrams = False
    else:
        cases = affected_cases(selected_paths)
        risk = classify(selected_paths)
        stage = target_stage(selected_paths, cases)
        verify_references = bool(reference_smoke_reasons(selected_paths))
        verify_diagrams = risk == "derived"

    operation = "pr" if event_name == "pull_request" else "main"

    # Stable main never replaces a model-verified result with only tool_verify.
    if operation == "main" and stage == "tool_verify":
        stage = "model_verify"

    if stage == "tool_qualification":
        verify_references = True
        verify_diagrams = True

    site_only = operation == "main" and stage == "none" and not (
        verify_references or verify_diagrams
    )
    needs_image = (
        stage in {"model_verify", "tool_qualification"}
        or verify_references
        or verify_diagrams
        or verify_pipeline
        or verify_contracts
    )
    release = operation == "main" and "scpf/pyproject.toml" in selected_paths

    return {
        "operation": operation,
        "risk": risk,
        "stage": stage,
        "cases": ",".join(cases),
        "verify_references": verify_references,
        "verify_diagrams": verify_diagrams,
        "verify_pipeline": verify_pipeline,
        "verify_contracts": verify_contracts,
        "needs_image": needs_image,
        "site_only": site_only,
        "release": release,
    }


def _write_outputs(path: Path, plan: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in plan.items():
            if isinstance(value, bool):
                value = "true" if value else "false"
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-action", default="")
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    parser.add_argument("--ref-name", default="")
    parser.add_argument("--schedule", default="")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    plan = make_plan(
        event_name=args.event_name,
        event_action=args.event_action,
        base=args.base,
        head=args.head,
        ref_name=args.ref_name,
        schedule=args.schedule,
    )
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.github_output:
        _write_outputs(args.github_output, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
