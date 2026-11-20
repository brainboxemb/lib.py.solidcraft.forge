#!/usr/bin/env python3
"""Run Forge reference evidence in the released reference runtime."""

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
    """Return the immutable released reference runtime image."""

    value = os.environ.get("REFERENCE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("REFERENCE_RUNTIME_IMAGE is required")
    return value


def source_sha() -> str:
    """Return the exact source commit whose evidence is being generated."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def reference_identity() -> tuple[str, str]:
    """Return model slug and implementation from the current nested item path."""

    value = os.environ.get("CAD_CI_ITEM_PATH", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM_PATH is required for verify_reference")

    path = Path(value)
    if path.is_absolute():
        repo_value = os.environ.get("CAD_CI_REPO", "").strip()
        if not repo_value:
            raise RuntimeError(
                "CAD_CI_REPO is required with an absolute CAD_CI_ITEM_PATH"
            )
        try:
            path = path.resolve().relative_to(Path(repo_value).resolve())
        except ValueError as exc:
            raise RuntimeError(
                "CAD_CI_ITEM_PATH must be inside CAD_CI_REPO"
            ) from exc

    parts = path.parts
    if len(parts) != 3 or parts[0] != "examples":
        raise RuntimeError(
            "reference item path must be examples/<model>/<implementation>"
        )
    return parts[1], parts[2]


def run_reference_validation(
    cases: str,
    *,
    implementations: str | None = None,
) -> None:
    """Run selected reference validation in the released runtime."""

    out = output_dir()
    image = runtime_image()
    subprocess.run(["docker", "pull", image], check=True)

    command = [
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
    ]
    if implementations is not None:
        command.extend(["--implementations", implementations])

    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


def verify_references(cases: str) -> None:
    """Run selected model reference sets and write structured evidence."""

    run_reference_validation(cases)


def verify_reference() -> None:
    """Run exactly the reference implementation represented by this CI item."""

    slug, implementation = reference_identity()
    run_reference_validation(
        slug,
        implementations=implementation,
    )


def main() -> int:
    """Dispatch the requested shared verification action."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=("verify_references", "verify_reference"),
    )
    parser.add_argument(
        "cases",
        nargs="?",
        help="all or a comma/space-separated model list for verify_references",
    )
    args = parser.parse_args()

    if args.operation == "verify_reference":
        if args.cases is not None:
            parser.error("verify_reference does not accept a cases argument")
        verify_reference()
        return 0

    verify_references(args.cases or "all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
