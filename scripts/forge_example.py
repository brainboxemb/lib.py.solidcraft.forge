"""Shared Forge-example mechanics for CI verification.

This module only owns mechanics that are common to Forge release verification
and per-model verification: locating the built wheel, running example-owned
contract tests, compiling a model with that exact wheel, and writing the
replayable SolidCraft command document.

It does not decide CI scope or verification policy.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def one_built_wheel(
    dist: Path,
    pattern: str = "scpf-*.whl",
    *,
    label: str = "Forge package",
) -> Path:
    """Return exactly one requested wheel from a CAD-CI output directory."""

    wheels = tuple(dist.glob(pattern))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one {label} wheel, found {len(wheels)}"
        )
    return wheels[0].resolve()


def dependency_wheel(
    name: str = "forge-tool",
    pattern: str = "scpf-*.whl",
) -> Path:
    """Return one exact wheel exposed by a CAD-CI dependency item."""

    raw = os.environ.get("CAD_CI_DEPENDENCIES_JSON", "").strip()
    if not raw:
        raise RuntimeError("CAD_CI_DEPENDENCIES_JSON is required")

    dependencies = json.loads(raw)
    dependency = dependencies.get(name)
    if not isinstance(dependency, dict):
        raise RuntimeError(f"{name} dependency context is required")

    output_root = dependency.get("output_root")
    if not isinstance(output_root, str) or not output_root:
        raise RuntimeError(f"{name} dependency output_root is required")

    return one_built_wheel(
        Path(output_root) / "dist",
        pattern,
        label=name,
    )


def python_environment(package: Path) -> dict[str, str]:
    """Return an environment that imports Forge from the built wheel."""

    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    parts = [str(package), str(ROOT)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_contract_tests(slug: str, package: Path) -> None:
    """Run one example's command-contract tests against the built wheel."""

    tests = ROOT / "examples" / slug / "tests"
    if not tests.is_dir():
        raise RuntimeError(f"missing contract-test directory: {tests}")

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
        env=python_environment(package),
        check=True,
    )


def compile_commands(slug: str, package: Path) -> dict:
    """Compile one Forge example to a replayable SolidCraft document."""

    package_text = str(package)
    if package_text not in sys.path:
        sys.path.insert(0, package_text)

    from scpf.runner import run_script

    model = ROOT / "examples" / slug / "scpf" / "model.py"
    if not model.is_file():
        raise RuntimeError(f"missing Forge model: {model}")

    document = run_script(model)
    if not isinstance(document, dict):
        raise RuntimeError("Forge model compilation did not return a document")

    commands = document.get("commands")
    if not isinstance(commands, list) or not commands:
        raise RuntimeError("Forge model compilation returned no commands")
    return document


def write_commands(document: dict, destination: Path) -> None:
    """Write one replayable command document deterministically."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
    )
