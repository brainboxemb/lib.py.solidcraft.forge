#!/usr/bin/env python3
"""Run shared Forge verification evidence in the released SolidCraft runtime."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def output_dir() -> Path:
    """Return the output directory supplied for the current CAD-CI item."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    path = Path(value).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_image() -> str:
    """Return the immutable released SolidCraft runtime image."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("FORGE_RUNTIME_IMAGE is required")
    return value


def source_sha() -> str:
    """Return the exact source commit whose evidence is being generated."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def verify_references(cases: str) -> None:
    """Run selected independent model references and write structured evidence."""

    out = output_dir()
    image = runtime_image()
    subprocess.run(["docker", "pull", image], check=True)
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/workspace:ro",
            "-v",
            f"{out}:/output",
            "-w",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/scpf:/workspace",
            image,
            "python",
            "/workspace/verification/reference_validation.py",
            "--cases",
            cases,
            "--out",
            "/output/references",
            "--source-sha",
            source_sha(),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Dispatch the requested shared verification action."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("verify_references",))
    parser.add_argument(
        "cases",
        nargs="?",
        default="all",
        help="all or a comma/space-separated model list",
    )
    args = parser.parse_args()
    verify_references(args.cases)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
