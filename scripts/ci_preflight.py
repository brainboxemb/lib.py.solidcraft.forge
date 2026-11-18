#!/usr/bin/env python3
"""Run cheap repository checks before CAD/reference qualification."""

from __future__ import annotations

import argparse
import compileall
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = ("scpf", "qualification", "site", "scripts", "examples")
WORKFLOW_KEYS = {
    "name",
    "run-name",
    "on",
    "permissions",
    "env",
    "defaults",
    "concurrency",
    "jobs",
}


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def check_python() -> None:
    failed = []
    for name in PYTHON_ROOTS:
        path = ROOT / name
        if path.exists() and not compileall.compile_dir(path, quiet=1):
            failed.append(name)
    if failed:
        raise RuntimeError("Python compile failed under: " + ", ".join(failed))


def check_workflows() -> None:
    for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        if not isinstance(data, dict):
            raise RuntimeError(f"{path}: workflow root must be a mapping")
        unknown = sorted(set(data) - WORKFLOW_KEYS)
        if unknown:
            raise RuntimeError(
                f"{path}: unexpected top-level workflow key(s): "
                + ", ".join(unknown)
            )
        jobs = data.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            raise RuntimeError(f"{path}: workflow must contain jobs")


def check_contract_tests() -> None:
    for pattern in (
        "test_preview_scope.py",
        "test_impact.py",
        "test_generated_output.py",
        "test_setup.py",
        "test_merge_promotion.py",
        "test_case_runner.py",
    ):
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "qualification/tests",
                "-p",
                pattern,
                "-v",
            ]
        )

    for pattern in (
        "test_publishing.py",
        "test_publish_generated.py",
        "test_reconcile_generated.py",
        "test_qualification_image.py",
    ):
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "site/tests",
                "-p",
                pattern,
                "-v",
            ]
        )


def check_site(source_sha: str, out: Path) -> None:
    run(
        [
            sys.executable,
            "site/build.py",
            "--out",
            str(out),
            "--source-sha",
            source_sha,
        ]
    )
    run(
        [
            sys.executable,
            "site/test_site.py",
            str(out),
            source_sha,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument(
        "--site-out",
        type=Path,
        default=ROOT / "output" / "site",
    )
    args = parser.parse_args()

    check_python()
    check_workflows()
    check_contract_tests()
    check_site(args.source_sha, args.site_out)
    print("Repository preflight PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
