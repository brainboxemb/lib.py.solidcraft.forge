#!/usr/bin/env python3
"""Build or unit-test the Forge Python tool for its generic CI item."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def output_root() -> Path:
    """Return the generic item output directory supplied by tool.cad.ci."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required for Forge tool CI")
    return Path(value).resolve()


def tool_build() -> None:
    """Build an installable wheel from the current Forge source tree."""

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
            str(ROOT / "scpf"),
        ],
        cwd=ROOT,
        check=True,
    )
    wheels = tuple(dist.glob("scpf-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"tool_build expected exactly one SCPF wheel, found {len(wheels)}"
        )


def tool_test() -> None:
    """Run the Forge library unit-test suite."""

    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(ROOT / "scpf" / "tests"),
            "-p",
            "test_*.py",
            "-v",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    """Dispatch the requested Forge tool stage."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("tool_build", "tool_test"))
    args = parser.parse_args()
    if args.operation == "tool_build":
        tool_build()
    else:
        tool_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
