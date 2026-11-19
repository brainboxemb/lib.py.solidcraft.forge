#!/usr/bin/env python3
"""Run host-side verification for one migrated Forge example."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def forge_package() -> Path:
    """Return the built Forge package exposed by the forge-tool dependency."""

    raw = os.environ.get("CAD_CI_DEPENDENCIES_JSON", "").strip()
    if not raw:
        raise RuntimeError("CAD_CI_DEPENDENCIES_JSON is required")
    dependencies = json.loads(raw)
    forge = dependencies.get("forge-tool")
    if not isinstance(forge, dict):
        raise RuntimeError("forge-tool dependency context is required")
    output_root = forge.get("output_root")
    if not isinstance(output_root, str) or not output_root:
        raise RuntimeError("forge-tool dependency output_root is required")
    wheels = tuple((Path(output_root) / "dist").glob("scpf-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one built Forge package, found {len(wheels)}"
        )
    return wheels[0].resolve()


def python_environment(package: Path) -> dict[str, str]:
    """Return an environment that imports Forge from the built package."""

    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    parts = [str(package), str(ROOT)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def item_slug() -> str:
    """Return the example slug selected by the generic CAD-CI item."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required")
    return value


def output_root() -> Path:
    """Return the output directory supplied for the current CAD-CI item."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def run_contract_tests(slug: str, package: Path) -> None:
    """Run the example-owned host-side contract tests against the built package."""

    tests = ROOT / "examples" / slug / "tests"
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
    """Compile the example model to its replayable SolidCraft document."""

    sys.path.insert(0, str(package))
    from scpf.runner import run_script

    model = ROOT / "examples" / slug / "scpf" / "model.py"
    document = run_script(model)
    if not isinstance(document, dict):
        raise RuntimeError("Forge model compilation did not return a document")
    commands = document.get("commands")
    if not isinstance(commands, list) or not commands:
        raise RuntimeError("Forge model compilation returned no commands")
    return document


def main() -> int:
    """Verify one example and write its replayable command document."""

    slug = item_slug()
    package = forge_package()
    run_contract_tests(slug, package)
    document = compile_commands(slug, package)

    destination = output_root() / "solidcraft.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Verified Forge example: {slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
