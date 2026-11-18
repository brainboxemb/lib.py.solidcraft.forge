#!/usr/bin/env python3
"""Run qualification tooling tests and tests owned by examples."""

from __future__ import annotations

from functools import lru_cache
import importlib.util
from io import TextIOBase
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def model_test_dirs(root: Path = ROOT) -> tuple[Path, ...]:
    """Return example test directories that contain unittest modules."""
    examples = Path(root) / "examples"
    if not examples.is_dir():
        return ()
    return tuple(
        tests
        for tests in sorted(examples.glob("*/tests"))
        if any(tests.glob("test_*.py"))
    )


def qualification_test_dirs(root: Path = ROOT) -> tuple[Path, ...]:
    """Return the directories that own qualification Python tests."""
    root = Path(root)
    return (root / "qualification" / "tests",) + model_test_dirs(root)


@lru_cache(maxsize=None)
def qualification_test_files(root: Path = ROOT) -> tuple[Path, ...]:
    """Discover the standard qualification test files once per repository root."""
    root = Path(root)
    files: list[Path] = []

    for test_dir in qualification_test_dirs(root):
        files.extend(sorted(test_dir.glob("test_*.py")))

    return tuple(files)


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    safe = re.sub(r"[^0-9A-Za-z_]+", "_", relative.as_posix())
    return f"_qualification_{safe}"


def _load_test_module(root: Path, path: Path):
    name = _module_name(root, path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load qualification test module: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_suite(root: Path = ROOT) -> unittest.TestSuite:
    """Load all discovered qualification tests into one in-memory test suite."""
    root = Path(root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for path in qualification_test_files(root):
        module = _load_test_module(root, path)
        suite.addTests(loader.loadTestsFromModule(module))

    return suite


def run(root: Path = ROOT, stream: TextIOBase | None = None) -> int:
    """Run the complete qualification Python suite in one process."""
    suite = build_suite(Path(root).resolve())
    result = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
    ).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run())
