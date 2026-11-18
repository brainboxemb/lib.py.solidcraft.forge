#!/usr/bin/env python3
"""Plan one Forge Actions run from event metadata and changed paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.impact import affected_cases, changed_paths, classify, final_gate
from qualification.preview_scope import reference_smoke_reasons


WEEKLY_FULL_CRON = "17 3 * * 1"
RECONCILE_CRON = "41 4 * * *"
FORGE_TRIGGER = ".github/workflows/forge.trigger"
REQUIRED_LEVEL = {
    "preflight": "",
    "regenerate-derived": "derived",
    "affected-q1-q2": "affected-q1-q2",
    "affected-q1-q6": "affected-q1-q6",
    "full-q1-q6": "q1-q6-full",
}

# Workflow/orchestration-only changes prove the complete machinery with one
# real native case instead of requalifying the entire catalog.
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
        "scripts/forge_scope.py",
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
    normalized = tuple(_norm(path) for path in paths)
    if not normalized:
        return False
    for path in normalized:
        if path in PIPELINE_PATHS:
            continue
        kind = classify((path,))
        if kind in {"presentation", "publication"}:
            continue
        return False
    return True


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
    if event_name == "pull_request" and event_action == "closed":
        return {
            "operation": "cleanup",
            "risk": "presentation",
            "gate": "preflight",
            "required_level": "",
            "cases": "",
            "reference_smoke": False,
            "pipeline_smoke": False,
            "contracts": False,
            "needs_image": False,
            "site_only": False,
            "release": False,
        }

    if event_name == "schedule" and schedule == RECONCILE_CRON:
        return {
            "operation": "reconcile",
            "risk": "presentation",
            "gate": "preflight",
            "required_level": "",
            "cases": "",
            "reference_smoke": False,
            "pipeline_smoke": False,
            "contracts": False,
            "needs_image": False,
            "site_only": False,
            "release": False,
        }

    if event_name == "workflow_dispatch" or (
        event_name == "schedule" and schedule == WEEKLY_FULL_CRON
    ):
        return {
            "operation": "main",
            "risk": "foundational",
            "gate": "full-q1-q6",
            "required_level": "q1-q6-full",
            "cases": "",
            "reference_smoke": True,
            "pipeline_smoke": False,
            "contracts": False,
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

    contracts = contract_snapshot_required(selected_paths)
    pipeline_smoke = pipeline_only(selected_paths)

    if event_name == "push" and FORGE_TRIGGER in selected_paths:
        gate = "full-q1-q6"
        cases = ()
        risk = "foundational"
        reference_smoke = True
        pipeline_smoke = False
    elif pipeline_smoke:
        gate = "preflight"
        cases = ()
        risk = "publication"
        reference_smoke = False
    else:
        cases = affected_cases(selected_paths)
        risk = classify(selected_paths)
        gate = final_gate(selected_paths, cases)
        reference_smoke = bool(reference_smoke_reasons(selected_paths))

    # Stable build/main is a native-qualified baseline. A main promotion may
    # not replace a previously Q1-Q6 case with only Q1-Q2 evidence.
    if event_name == "push" and gate == "affected-q1-q2":
        gate = "affected-q1-q6"

    operation = "pr" if event_name == "pull_request" else "main"
    site_only = operation == "main" and gate == "preflight"
    needs_image = (
        gate in {"affected-q1-q6", "full-q1-q6"}
        or reference_smoke
        or pipeline_smoke
        or contracts
    )

    release = (
        operation == "main"
        and "scpf/pyproject.toml" in selected_paths
    )

    return {
        "operation": operation,
        "risk": risk,
        "gate": gate,
        "required_level": REQUIRED_LEVEL[gate],
        "cases": ",".join(cases),
        "reference_smoke": reference_smoke,
        "pipeline_smoke": pipeline_smoke,
        "contracts": contracts,
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
