#!/usr/bin/env python3
"""Run qualification tooling tests and tests owned by examples."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def model_test_dirs(root: Path = ROOT) -> tuple[Path, ...]:
    """Return example test directories that contain unittest modules."""
    examples = root / "examples"
    if not examples.is_dir():
        return ()
    return tuple(
        tests
        for tests in sorted(examples.glob("*/tests"))
        if any(tests.glob("test_*.py"))
    )


def qualification_test_dirs(root: Path = ROOT) -> tuple[Path, ...]:
    """Return every directory in the standard qualification Python suite."""
    return (root / "qualification" / "tests",) + model_test_dirs(root)


def run(root: Path = ROOT) -> int:
    """Run each test directory independently and return a process-style status."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    failed = False

    for test_dir in qualification_test_dirs(root):
        print(f"\n== {test_dir.relative_to(root)} ==")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(test_dir),
                "-p",
                "test_*.py",
                "-v",
            ],
            cwd=root,
            env=env,
            check=False,
        )
        failed = failed or completed.returncode != 0

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
