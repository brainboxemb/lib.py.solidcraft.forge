#!/usr/bin/env python3
"""Run Forge-owned generated qualification evidence inside the resolved image.

The generic CI tool supplies item identity/output paths. Forge supplies the
immutable runtime image and decides whether reference or diagram evidence is
required for the current gate.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def output_dir() -> Path:
    """Return the current generic item output directory."""

    value = os.environ.get("CAD_CI_OUTPUT")
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required for qualification evidence CI")
    return Path(value).resolve()


def qualification_image() -> str:
    """Return the immutable qualification runtime image selected by Forge."""

    value = os.environ.get("FORGE_QUALIFICATION_IMAGE", "").strip()
    if not value:
        raise RuntimeError(
            "FORGE_QUALIFICATION_IMAGE is required for qualification evidence CI"
        )
    return value


def source_sha() -> str:
    """Return the exact source commit whose evidence is being generated."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def docker_python(*args: str) -> None:
    """Run one Forge evidence command inside the qualification image."""

    out = output_dir()
    relative = out.relative_to(ROOT)
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/workspace",
            "-w",
            "/workspace",
            "-e",
            "PYTHONPATH=/workspace/scpf:/workspace",
            qualification_image(),
            "python",
            *args,
        ],
        cwd=ROOT,
        check=True,
    )


def run_references() -> None:
    """Build the complete external-library reference evidence set."""

    relative = output_dir().relative_to(ROOT)
    docker_python(
        "qualification/reference_validation.py",
        "--cases",
        "all",
        "--out",
        f"/workspace/{relative.as_posix()}/references",
        "--source-sha",
        source_sha(),
    )


def run_diagrams() -> None:
    """Build the complete generated qualification diagram set."""

    relative = output_dir().relative_to(ROOT)
    docker_python(
        "qualification/render_diagrams.py",
        "--out",
        f"/workspace/{relative.as_posix()}/rendered",
    )


def main() -> int:
    """Dispatch the Forge-owned evidence item operation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("references", "diagrams"))
    args = parser.parse_args()
    if args.operation == "references":
        run_references()
    else:
        run_diagrams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
