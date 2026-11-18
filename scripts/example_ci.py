#!/usr/bin/env python3
"""Run native CI for the Forge example that owns the current tool.cad.ci item.

tool.cad.ci supplies the item identity and output directory. Forge decides when
native SolidCraft is required, selects the immutable runtime image and owns all
case-specific validation through qualification.case_runner.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def item_slug() -> str:
    """Return the example slug from the current generic CI item."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required when running example CI")
    return value


def native_output() -> Path:
    """Return the build directory reserved for this item's native evidence."""

    value = os.environ.get("CAD_CI_OUTPUT")
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required when running example CI")
    return Path(value).resolve() / "native-case"


def qualification_image() -> str:
    """Return the immutable native runtime image selected by Forge."""

    value = os.environ.get("FORGE_QUALIFICATION_IMAGE", "").strip()
    if not value:
        raise RuntimeError(
            "FORGE_QUALIFICATION_IMAGE is required for native example CI"
        )
    return value


def run_native() -> None:
    """Run the existing Forge native stages for the current example item."""

    slug = item_slug()
    out = native_output()
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
            "compile",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Dispatch the example-owned CI operation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("native",))
    args = parser.parse_args()
    if args.operation == "native":
        run_native()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
