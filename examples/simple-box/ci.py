#!/usr/bin/env python3
"""Run CI behaviour owned by the simple-box example.

tool.cad.ci provides the item output directory and executes this script. Forge
still owns the native case runner, runtime image and SolidCraft validation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def native_output() -> Path:
    """Return the build directory reserved for this case's native evidence."""

    value = os.environ.get("CAD_CI_OUTPUT")
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required when running case CI")
    return Path(value).resolve() / "native-case"


def qualification_image() -> str:
    """Return the immutable native runtime image selected by Forge."""

    value = os.environ.get("FORGE_QUALIFICATION_IMAGE", "").strip()
    if not value:
        raise RuntimeError(
            "FORGE_QUALIFICATION_IMAGE is required for native case CI"
        )
    return value


def run_native() -> None:
    """Run the existing Forge native stages inside the resolved runtime image."""

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
            "simple-box",
            "--out",
            f"/workspace/{relative_out.as_posix()}",
            "--from",
            "compile",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Dispatch the case-owned CI operation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("native",))
    args = parser.parse_args()

    if args.operation == "native":
        run_native()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
