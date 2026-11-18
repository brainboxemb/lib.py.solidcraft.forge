#!/usr/bin/env python3
"""Run the verification gate selected by qualification.impact."""

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
    subprocess.run(command, cwd=cwd, check=True)


def selected_cases(value: str, gate: str) -> tuple[str, ...]:
    if gate == "full-q1-q6":
        return tuple(TECHNICAL_CASE_SLUGS)
    if not value.strip():
        selected = ()
    else:
        selected = tuple(
            slug
            for slug in parse_case_selection(value)
            if slug in TECHNICAL_CASE_SLUGS
        )
    if gate not in {"preflight", "regenerate-derived"} and not selected:
        raise ValueError(f"{gate} requires supported affected cases")
    return selected


def run_q1_q2(cases: tuple[str, ...], out: Path) -> None:
    qualification = out / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT / "scpf",
    )
    run([sys.executable, "qualification/testsuite.py"])
    case_arg = ",".join(cases)
    for level in ("q1", "q2"):
        run(
            [
                sys.executable,
                "qualification/run_case_evidence.py",
                "--level",
                level,
                "--cases",
                case_arg,
                "--out",
                str(qualification),
            ]
        )
    for slug in cases:
        run(
            [
                sys.executable,
                "-m",
                "scpf",
                f"examples/{slug}/scpf/model.py",
                "--out",
                str(out / f"{slug}.json"),
            ]
        )


def run_gate(
    *,
    gate: str,
    cases: tuple[str, ...],
    out: Path,
    source_sha: str,
    reference_smoke: bool,
) -> None:
    if out.exists():
        import shutil
        shutil.rmtree(out)
    out.mkdir(parents=True)

    if gate == "preflight":
        return
    if gate == "regenerate-derived":
        run(
            [
                sys.executable,
                "qualification/render_diagrams.py",
                "--out",
                str(out / "diagrams"),
            ]
        )
        return
    if gate == "affected-q1-q2":
        run_q1_q2(cases, out)
    elif gate in {"affected-q1-q6", "full-q1-q6"}:
        run(
            [
                sys.executable,
                "qualification/run_affected.py",
                "--cases",
                ",".join(cases),
                "--out",
                str(out),
            ]
        )
    else:
        raise ValueError(f"unknown gate: {gate}")

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
    if gate == "preflight":
        return
    level = {
        "regenerate-derived": "derived",
        "affected-q1-q2": "affected-q1-q2",
        "affected-q1-q6": "affected-q1-q6",
        "full-q1-q6": "q1-q6-full",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--cases", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--reference-smoke", action="store_true")
    parser.add_argument("--build-out", type=Path)
    parser.add_argument("--scope", choices=("main", "pr"), default="pr")
    parser.add_argument("--source-ref")
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--base-commit")
    parser.add_argument("--workflow-run-id")
    args = parser.parse_args()

    cases = selected_cases(args.cases, args.gate)
    run_gate(
        gate=args.gate,
        cases=cases,
        out=args.out,
        source_sha=args.source_sha,
        reference_smoke=args.reference_smoke,
    )

    if args.build_out:
        if not (args.source_ref and args.workflow_run_id):
            raise SystemExit(
                "--build-out requires --source-ref and --workflow-run-id"
            )
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
