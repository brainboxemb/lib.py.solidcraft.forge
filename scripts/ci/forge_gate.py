#!/usr/bin/env python3
"""Run the qualification gate selected by forge_plan.py."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def command_for(
    plan: dict,
    *,
    source_sha: str,
    source_ref: str,
    workflow_run_id: str,
    out: Path,
    build_out: Path,
    base_commit: str = "",
) -> list[str] | None:
    if not plan.get("has_build"):
        return None

    command = [
        sys.executable,
        "scripts/verification_gate.py",
        "--gate",
        plan["gate"],
        "--out",
        str(out),
        "--source-sha",
        source_sha,
        "--build-out",
        str(build_out),
        "--scope",
        "pr" if plan["publication"] == "preview" else "main",
        "--source-ref",
        source_ref,
        "--workflow-run-id",
        workflow_run_id,
    ]

    cases = tuple(plan.get("cases") or ())
    if cases:
        command += ["--cases", ",".join(cases)]
    if plan.get("reference_smoke"):
        command.append("--reference-smoke")

    pull_request = plan.get("pull_request")
    if plan["publication"] == "preview":
        if not pull_request:
            raise ValueError("preview qualification requires pull_request")
        command += ["--pull-request", str(pull_request)]
        if base_commit:
            command += ["--base-commit", base_commit]

    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--base-commit", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--build-out", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    command = command_for(
        plan,
        source_sha=args.source_sha,
        source_ref=args.source_ref,
        workflow_run_id=args.workflow_run_id,
        out=args.out,
        build_out=args.build_out,
        base_commit=args.base_commit,
    )
    if command is None:
        print("No technical qualification selected.")
        return 0
    subprocess.run(command, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
