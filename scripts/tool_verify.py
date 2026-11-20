#!/usr/bin/env python3
"""Release-verify the built Forge package with the fixed example set."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from forge_example import (
    compile_commands,
    dependency_wheel,
    run_contract_tests,
    write_commands,
)


ROOT = Path(__file__).resolve().parents[1]

# These are Forge release checks, not the historical model-verification catalog.
PASSING_EXAMPLES = (
    "simple-box",
    "anchored-holes",
    "components",
    "corner-anchor",
)

EXPECTED_REJECTIONS = {
    "custom-anchor": (
        "rotated Placement in a normal attachment is not supported yet"
    ),
}


def output_root() -> Path:
    """Return the Forge tool item's CAD-CI output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def verify_passing_example(slug: str, package: Path, destination: Path) -> None:
    """Run command-contract tests and compile one supported release example."""

    run_contract_tests(slug, package)
    document = compile_commands(slug, package)
    write_commands(document, destination / slug / "solidcraft.json")


def verify_expected_rejection(
    slug: str,
    expected_message: str,
    package: Path,
    destination: Path,
) -> None:
    """Prove that one intentionally unsupported example fails clearly."""

    package_text = str(package)
    if package_text not in sys.path:
        sys.path.insert(0, package_text)

    from scpf.compiler import ModelError

    try:
        compile_commands(slug, package)
    except ModelError as exc:
        message = str(exc)
        if expected_message not in message:
            raise RuntimeError(
                f"{slug}: unexpected Forge rejection: {message}"
            ) from exc

        record = {
            "example": slug,
            "status": "expected-rejection",
            "message": message,
        }
        target = destination / slug / "blocked.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(record, indent=2) + "\n",
            encoding="utf-8",
        )
        return

    raise RuntimeError(f"{slug}: expected Forge to reject this example")


def main() -> int:
    """Run the complete Forge release-verification example set."""

    output = output_root()
    package = dependency_wheel("forge-package")
    destination = output / "tool_verify"

    for slug in PASSING_EXAMPLES:
        verify_passing_example(slug, package, destination)

    for slug, message in EXPECTED_REJECTIONS.items():
        verify_expected_rejection(slug, message, package, destination)

    print(
        "Forge release verification passed: "
        + ", ".join(PASSING_EXAMPLES + tuple(EXPECTED_REJECTIONS))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
