#!/usr/bin/env python3
"""Run host-side verification for one migrated Forge example."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


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


def run_contract_tests(slug: str) -> None:
    """Run the example-owned host-side contract tests."""

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
        check=True,
    )


def compile_commands(slug: str) -> dict:
    """Compile the example model to its replayable SolidCraft document."""

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
    run_contract_tests(slug)
    document = compile_commands(slug)

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
