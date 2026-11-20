#!/usr/bin/env python3
"""Build the exact released CAD verification library wheel once for CAD-CI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "verification" / "library" / "requirements.txt"


def output_root() -> Path:
    """Return the output directory supplied to the dependency item."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def built_wheel() -> Path:
    """Return the one released verification-library wheel."""

    wheels = tuple(
        (output_root() / "dist").glob(
            "brainboxemb_cad_verification_lib-*.whl"
        )
    )
    if len(wheels) != 1:
        raise RuntimeError(
            "expected exactly one CAD verification library wheel, "
            f"found {len(wheels)}"
        )
    return wheels[0]


def build() -> None:
    """Build one pure-Python wheel without reinstalling runtime dependencies."""

    dist = output_root() / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(dist),
            "-r",
            str(REQUIREMENTS),
        ],
        cwd=ROOT,
        check=True,
    )
    built_wheel()


def main() -> int:
    """Dispatch the explicit dependency build operation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("build",))
    args = parser.parse_args()
    if args.operation == "build":
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
