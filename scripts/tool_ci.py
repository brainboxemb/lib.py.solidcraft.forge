#!/usr/bin/env python3
"""Build or unit-test the Forge Python tool for its CI item."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def output_root() -> Path:
    """Return the output directory supplied for the current CI item."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def tool_build() -> None:
    """Build one installable Forge wheel without running verification."""

    dist = output_root() / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    # Use the PEP 517 build environment declared by scpf/pyproject.toml.
    # The CI runner therefore does not need build backends installed globally.
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
    """Run the Forge/SCPF unit-test suite."""

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
    """Dispatch the requested Forge tool step."""

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
