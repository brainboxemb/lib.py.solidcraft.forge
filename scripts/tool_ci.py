#!/usr/bin/env python3
"""Build and unit-test the Forge Python package for its CAD-CI item."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

from forge_example import dependency_wheel


ROOT = Path(__file__).resolve().parents[1]


def output_root() -> Path:
    """Return the generic item output directory supplied by CAD CI."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def built_wheel() -> Path:
    """Return the one Forge wheel produced by tool_build."""

    wheels = tuple((output_root() / "dist").glob("scpf-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one SCPF wheel, found {len(wheels)}"
        )
    return wheels[0]


def tool_build() -> None:
    """Build one installable Forge wheel into this item's output tree."""

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
    built_wheel()


def tool_test() -> None:
    """Install the built wheel and run the Forge/SCPF unit-test suite."""

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            str(dependency_wheel("forge-package")),
        ],
        cwd=ROOT,
        check=True,
    )
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
    """Dispatch one explicit Forge-tool CI step."""

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
