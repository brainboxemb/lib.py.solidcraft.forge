#!/usr/bin/env python3
"""Run CI owned by one Forge example item.

The generic CI tool supplies the item identity and output directory. Forge owns
the integration tests, command compilation, native SolidCraft runtime and all
qualification checks.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def item_slug() -> str:
    """Return the example slug from the generic CI item identity."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required when running example CI")
    return value


def case_output() -> Path:
    """Return the staged case directory inside this item output."""

    value = os.environ.get("CAD_CI_OUTPUT")
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required when running example CI")
    return Path(value).resolve() / "case"


def source_sha() -> str:
    """Return the exact source commit represented by this item output."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def qualification_image() -> str:
    """Return the immutable native runtime image selected by Forge."""

    value = os.environ.get("FORGE_QUALIFICATION_IMAGE", "").strip()
    if not value:
        raise RuntimeError(
            "FORGE_QUALIFICATION_IMAGE is required for native example CI"
        )
    return value


def run_integration() -> None:
    """Run the example command-contract tests, then compile its command JSON."""

    slug = item_slug()
    tests = ROOT / "examples" / slug / "tests"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(tests),
            "-p",
            "test_*.py",
            "-v",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "qualification" / "case_runner.py"),
            slug,
            "--out",
            str(case_output()),
            "--stage",
            "compile",
        ],
        cwd=ROOT,
        check=True,
    )


def run_native() -> None:
    """Resume the compiled case at native replay inside the selected image."""

    slug = item_slug()
    out = case_output()
    relative_out = out.relative_to(ROOT)
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
            "qualification/case_runner.py",
            slug,
            "--out",
            f"/workspace/{relative_out.as_posix()}",
            "--from",
            "replay",
        ],
        cwd=ROOT,
        check=True,
    )

    # Normalization is host-side and reads only files produced by the item.
    # It does not rerun SolidCraft or duplicate any native check.
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "qualification" / "finalize_item_result.py"),
            slug,
            "--out",
            str(out),
            "--source-sha",
            source_sha(),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Dispatch the example-owned CI operation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("integration", "native"))
    args = parser.parse_args()

    if args.operation == "integration":
        run_integration()
    else:
        run_native()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
