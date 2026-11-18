#!/usr/bin/env python3
"""Run staged CI for the Forge example that owns the current tool.cad.ci item.

tool.cad.ci supplies the item identity and output directory. Forge owns the
meaning of the integration/native stages, selects the immutable native runtime
image and keeps all SolidCraft validation in qualification.case_runner.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def item_slug() -> str:
    """Return the example slug from the current generic CI item."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required when running example CI")
    return value


def case_output() -> Path:
    """Return the shared staged case directory inside this item output."""

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
    """Run cheap case evidence and command compilation on the host."""

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "qualification" / "case_runner.py"),
            item_slug(),
            "--out",
            str(case_output()),
            "--until",
            "compile",
        ],
        cwd=ROOT,
        check=True,
    )


def run_native() -> None:
    """Resume the same staged case output at replay inside the native image."""

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

    # Keep the durable generic item self-contained. This normalization consumes
    # only the staged files just produced above and does not rerun SolidCraft.
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
