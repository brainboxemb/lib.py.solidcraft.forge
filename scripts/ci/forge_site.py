#!/usr/bin/env python3
"""Build and test one Forge site from one resolved technical build."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build_site(
    *,
    build_root: Path,
    out: Path,
    source_sha: str,
    build_commit: str,
    build_scope: str,
    stage: str,
    source_ref: str,
    workflow_run_id: str,
    pull_request: int | None = None,
    require_native: bool = False,
    require_references: bool = False,
) -> None:
    evidence = out.parent / "evidence"
    run([
        sys.executable,
        "scripts/generated_output.py",
        "materialize-site-evidence",
        "--build-root",
        str(build_root),
        "--destination",
        str(evidence),
    ])

    run([
        sys.executable,
        "site/build.py",
        "--out",
        str(out),
        "--source-sha",
        source_sha,
        "--native",
        str(evidence / "native"),
        "--references",
        str(evidence / "references"),
        "--diagram-root",
        str(evidence / "diagrams"),
        "--build-manifest",
        str(build_root / "build.json"),
        "--build-commit",
        build_commit,
        "--build-scope",
        build_scope,
    ])

    test = [
        sys.executable,
        "site/test_site.py",
        str(out),
        source_sha,
        f"--build-commit={build_commit}",
    ]
    if require_native:
        test.append("--require-native")
    if require_references:
        test.append("--require-references")
    run(test)

    provenance = [
        sys.executable,
        "site/provenance.py",
        "write-build",
        "--out",
        str(out / "provenance.json"),
        "--stage",
        stage,
        "--source-ref",
        source_ref,
        "--source-commit",
        source_sha,
        "--build-commit",
        build_commit,
        "--build-manifest",
        str(build_root / "build.json"),
        "--workflow-run-id",
        workflow_run_id,
    ]
    if pull_request is not None:
        provenance += ["--pull-request", str(pull_request)]
    run(provenance)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--build-commit", required=True)
    parser.add_argument("--build-scope", required=True)
    parser.add_argument("--stage", choices=("preview", "stable"), required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--require-native", action="store_true")
    parser.add_argument("--require-references", action="store_true")
    args = parser.parse_args()

    build_site(
        build_root=args.build_root,
        out=args.out,
        source_sha=args.source_sha,
        build_commit=args.build_commit,
        build_scope=args.build_scope,
        stage=args.stage,
        source_ref=args.source_ref,
        workflow_run_id=args.workflow_run_id,
        pull_request=args.pull_request,
        require_native=args.require_native,
        require_references=args.require_references,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
