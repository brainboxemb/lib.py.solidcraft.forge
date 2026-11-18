#!/usr/bin/env python3
"""Select the one Forge workflow path from an event and source diff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.impact import (
    affected_cases,
    changed_paths,
    classify,
    final_gate,
)
from qualification.preview_scope import reference_smoke_reasons


FULL_GATE = "full-q1-q6"
TRIGGER_PATH = "scripts/ci/forge.trigger"
PIPELINE_SMOKE_CASE = "simple-box"
PIPELINE_SMOKE_PATHS = (
    ".github/workflows/forge.yml",
    "scripts/ci/forge_plan.py",
    "scripts/ci/forge_gate.py",
    "scripts/ci/forge_site.py",
    "scripts/ci/forge_release.py",
    "scripts/generated_output.py",
    "scripts/verification_gate.py",
    "site/build.py",
)

PIPELINE_ONLY_EXACT = frozenset(
    {
        "AGENTS.md",
        "qualification/impact.py",
        "docs/10-release-process.md",
        "docs/11-generated-output.md",
        "docs/changes/0041-one-forge-workflow.md",
        "docs/changes/README.md",
    }
)
PIPELINE_ONLY_PREFIXES = (
    ".github/workflows/",
    "scripts/ci/",
    "site/tests/",
)

CONTRACT_PATHS = (
    "scpf/scpf/",
    "scripts/solidcraft_snapshot.py",
    "docs/vendor/solidcraft/",
    "qualification/toolchain.json",
)


def pipeline_smoke_required(paths: tuple[str, ...]) -> bool:
    return any(path in PIPELINE_SMOKE_PATHS for path in paths)


def pipeline_only_change(paths: tuple[str, ...]) -> bool:
    """True only for a CI/workflow refactor with no product/toolchain change."""
    return bool(paths) and pipeline_smoke_required(paths) and all(
        path in PIPELINE_ONLY_EXACT
        or any(path.startswith(prefix) for prefix in PIPELINE_ONLY_PREFIXES)
        for path in paths
    )


def contract_check_required(paths: tuple[str, ...]) -> bool:
    return any(
        path == prefix or path.startswith(prefix)
        for path in paths
        for prefix in CONTRACT_PATHS
    )


def make_plan(
    *,
    event_name: str,
    base: str,
    head: str,
    ref_name: str,
    pull_request: int | None = None,
) -> dict:
    forced_full = event_name in {"workflow_dispatch", "schedule"}
    paths: tuple[str, ...] = ()
    if not forced_full and base and head:
        paths = changed_paths(base, head)

    cases = affected_cases(paths)
    risk = classify(paths)
    gate = final_gate(paths, cases)

    if forced_full or TRIGGER_PATH in paths:
        gate = FULL_GATE
        cases = ()

    if (
        event_name == "pull_request"
        and not forced_full
        and pipeline_only_change(paths)
    ):
        gate = "affected-q1-q6"
        cases = (PIPELINE_SMOKE_CASE,)

    # Main is intentionally simple: presentation-only may reuse the complete
    # baseline; every technical main change gets one full qualification.
    if event_name == "push" and ref_name == "main" and gate != "preflight":
        gate = FULL_GATE
        cases = ()

    reference_reasons = reference_smoke_reasons(paths)
    publication = (
        "preview"
        if event_name == "pull_request"
        else "stable"
        if ref_name == "main"
        else "none"
    )

    return {
        "schema": 1,
        "event_name": event_name,
        "ref_name": ref_name,
        "pull_request": pull_request,
        "paths": list(paths),
        "risk": risk,
        "gate": gate,
        "cases": list(cases),
        "has_build": gate != "preflight",
        "site_only": gate == "preflight",
        "reference_smoke": bool(reference_reasons),
        "reference_reasons": list(reference_reasons),
        "contracts": forced_full or contract_check_required(paths),
        "publication": publication,
        "full": gate == FULL_GATE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    plan = make_plan(
        event_name=args.event_name,
        base=args.base,
        head=args.head,
        ref_name=args.ref_name,
        pull_request=args.pull_request,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(plan, indent=2))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            for key in (
                "gate",
                "has_build",
                "site_only",
                "reference_smoke",
                "contracts",
                "publication",
                "full",
            ):
                value = plan[key]
                if isinstance(value, bool):
                    value = "true" if value else "false"
                handle.write(f"{key}={value}\n")
            handle.write(f"cases={','.join(plan['cases'])}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
