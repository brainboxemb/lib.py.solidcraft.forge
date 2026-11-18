#!/usr/bin/env python3
"""Assemble a Forge native gate from completed tool.cad.ci example items.

Example items have already run the real case stages. This module collects that
evidence, adds Forge-owned reference/diagram output when policy requires it and
writes the transitional build format used by the current site publisher.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.collect_item_results import collect_from_items
from scripts.verification_gate import assemble_build, selected_cases


NATIVE_GATES = {"affected-q1-q6", "full-q1-q6"}


def run(command: list[str]) -> None:
    """Run one Forge-owned post-qualification command."""

    subprocess.run(command, cwd=ROOT, check=True)


def execute(
    *,
    gate: str,
    cases_value: str,
    out: Path,
    build_out: Path,
    source_sha: str,
    reference_smoke: bool,
    scope: str,
    source_ref: str,
    pull_request: int | None,
    base_commit: str | None,
    workflow_run_id: str,
    build_root: Path = ROOT / "build",
) -> tuple[str, ...]:
    """Collect completed native items and assemble current publication input."""

    if gate not in NATIVE_GATES:
        raise ValueError(f"item native gate does not support {gate}")
    cases = selected_cases(cases_value, gate)

    collect_from_items(
        build_root=build_root,
        out=out,
        cases=cases,
        source_sha=source_sha,
    )

    # Reference implementations and diagrams are Forge publication evidence.
    # They are intentionally outside the generic item runner.
    if reference_smoke or gate == "full-q1-q6":
        run(
            [
                sys.executable,
                "qualification/reference_validation.py",
                "--cases",
                ",".join(cases),
                "--out",
                str(out / "references"),
                "--source-sha",
                source_sha,
            ]
        )
    if gate == "full-q1-q6":
        run(
            [
                sys.executable,
                "qualification/render_diagrams.py",
                "--out",
                str(out / "diagrams"),
            ]
        )

    assemble_build(
        gate=gate,
        cases=cases,
        out=out,
        build_out=build_out,
        scope=scope,
        source_ref=source_ref,
        source_sha=source_sha,
        pull_request=pull_request,
        base_commit=base_commit,
        workflow_run_id=workflow_run_id,
    )
    return cases


def main() -> int:
    """Parse pipeline arguments and build the native gate from item output."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=sorted(NATIVE_GATES), required=True)
    parser.add_argument("--cases", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--build-out", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, default=ROOT / "build")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--reference-smoke", action="store_true")
    parser.add_argument("--scope", choices=("main", "pr"), required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--base-commit")
    parser.add_argument("--workflow-run-id", required=True)
    args = parser.parse_args()

    if args.scope == "pr" and not args.pull_request:
        raise SystemExit("--scope pr requires --pull-request")

    execute(
        gate=args.gate,
        cases_value=args.cases,
        out=args.out,
        build_out=args.build_out,
        build_root=args.build_root,
        source_sha=args.source_sha,
        reference_smoke=args.reference_smoke,
        scope=args.scope,
        source_ref=args.source_ref,
        pull_request=args.pull_request,
        base_commit=args.base_commit,
        workflow_run_id=args.workflow_run_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
