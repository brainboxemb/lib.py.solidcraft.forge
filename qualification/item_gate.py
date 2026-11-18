#!/usr/bin/env python3
"""Assemble a Forge native gate from completed tool.cad.ci item output.

Example items already contain the real case stages. Reference and diagram
evidence are separate generic items. This module only translates those
consumer-owned outputs into the transitional Forge build shape still used by
the current site publisher.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.collect_item_results import collect_from_items
from scripts.verification_gate import assemble_build, selected_cases


NATIVE_GATES = {"affected-q1-q6", "full-q1-q6"}


def copy_completed_item_output(
    *,
    build_root: Path,
    item_path: Path,
    output_name: str,
    destination: Path,
) -> None:
    """Copy one declared output from a complete passing generic CI item."""

    item_root = build_root / item_path
    try:
        state = json.loads(
            (item_root / "item.json").read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing completed evidence item: {item_path}") from exc
    if state.get("status") != "pass":
        raise RuntimeError(f"evidence item is not passing: {item_path}")

    source = item_root / output_name
    if not source.is_dir() or not any(source.iterdir()):
        raise RuntimeError(
            f"missing evidence output {output_name!r} for {item_path}"
        )
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


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
    """Collect completed CI items and assemble current publication input."""

    if gate not in NATIVE_GATES:
        raise ValueError(f"item native gate does not support {gate}")
    cases = selected_cases(cases_value, gate)

    collect_from_items(
        build_root=build_root,
        out=out,
        cases=cases,
        source_sha=source_sha,
    )

    # These are normal generic CI items. Forge knows what their files mean;
    # tool.cad.ci only guarantees that the item output is complete and current.
    if reference_smoke or gate == "full-q1-q6":
        copy_completed_item_output(
            build_root=build_root,
            item_path=Path("qualification/reference_suite"),
            output_name="references",
            destination=out / "references",
        )
    if gate == "full-q1-q6":
        copy_completed_item_output(
            build_root=build_root,
            item_path=Path("qualification/diagrams"),
            output_name="rendered",
            destination=out / "diagrams",
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
