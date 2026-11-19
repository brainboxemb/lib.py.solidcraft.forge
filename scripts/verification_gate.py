#!/usr/bin/env python3
"""Translate a semantic Forge gate into the transitional generated-build form.

Native and integration execution already happens through tool.cad.ci items.
This module only keeps the old generated-build adapter working until the build
and Pages cut-over removes that format completely.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.cases import supported_case_slugs
from qualification.case_selection import parse_case_selection
from qualification.project_metadata import scpf_version
from scpf.version import TESTED_SOLIDCRAFT_VERSION


TECHNICAL_CASE_SLUGS = supported_case_slugs()


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    """Run one repository-owned adapter command."""

    subprocess.run(command, cwd=cwd, check=True)


def selected_cases(value: str, gate: str) -> tuple[str, ...]:
    """Resolve the concrete example set selected by Forge policy."""

    if gate == "full-native":
        return tuple(TECHNICAL_CASE_SLUGS)

    selected = (
        tuple(
            slug
            for slug in parse_case_selection(value)
            if slug in TECHNICAL_CASE_SLUGS
        )
        if value.strip()
        else ()
    )
    if gate in {"affected-integration", "affected-native"} and not selected:
        raise ValueError(f"{gate} requires supported affected cases")
    return selected


def assemble_build(
    *,
    gate: str,
    cases: tuple[str, ...],
    out: Path,
    build_out: Path,
    scope: str,
    source_ref: str,
    source_sha: str,
    pull_request: int | None,
    base_commit: str | None,
    workflow_run_id: str,
) -> None:
    """Package already-produced item output for the transitional build format."""

    if gate == "preflight":
        return
    level = {
        "regenerate-derived": "derived",
        "affected-integration": "integration",
        "affected-native": "native",
        "full-native": "full-native",
    }[gate]
    run(
        [
            sys.executable,
            "scripts/generated_output.py",
            "assemble-build",
            "--output-root",
            str(out),
            "--destination",
            str(build_out),
            "--scope",
            scope,
            "--source-ref",
            source_ref,
            "--source-commit",
            source_sha,
            *(
                ["--pull-request", str(pull_request)]
                if pull_request is not None
                else []
            ),
            *(
                ["--base-commit", base_commit]
                if base_commit
                else []
            ),
            "--forge-version",
            scpf_version(),
            "--solidcraft-version",
            TESTED_SOLIDCRAFT_VERSION,
            "--workflow-run-id",
            workflow_run_id,
            "--qualification-level",
            level,
            "--qualification-status",
            "pass",
            "--cases",
            ",".join(cases),
        ]
    )


def main() -> int:
    """Expose the transitional build adapter for local diagnostics."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--cases", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--build-out", type=Path)
    parser.add_argument("--scope", choices=("main", "pr"), default="pr")
    parser.add_argument("--source-ref")
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--base-commit")
    parser.add_argument("--workflow-run-id")
    # Kept for CLI compatibility during the cut-over; execution is item-owned.
    parser.add_argument("--reference-smoke", action="store_true")
    args = parser.parse_args()

    cases = selected_cases(args.cases, args.gate)
    if not args.build_out:
        return 0
    if not (args.source_ref and args.workflow_run_id):
        raise SystemExit("--build-out requires --source-ref and --workflow-run-id")
    if args.scope == "pr" and not args.pull_request:
        raise SystemExit("--scope pr requires --pull-request")
    assemble_build(
        gate=args.gate,
        cases=cases,
        out=args.out,
        build_out=args.build_out,
        scope=args.scope,
        source_ref=args.source_ref,
        source_sha=args.source_sha,
        pull_request=args.pull_request,
        base_commit=args.base_commit,
        workflow_run_id=args.workflow_run_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
