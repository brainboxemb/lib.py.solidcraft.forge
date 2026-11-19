#!/usr/bin/env python3
"""Compile and verify one Forge model in the pinned SolidCraft runtime."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from forge_example import compile_commands, dependency_wheel, write_commands


ROOT = Path(__file__).resolve().parents[1]


def item_slug() -> str:
    """Return the model selected by CAD-CI."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required")
    return value


def output_root() -> Path:
    """Return this CAD-CI model item's materialized output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def runtime_image() -> str:
    """Return the immutable runtime prepared before the CAD-CI run."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("FORGE_RUNTIME_IMAGE is required for model_verify")
    return value


def main() -> int:
    """Compile with the built Forge wheel, then run model-owned verification."""

    slug = item_slug()
    output = output_root()
    wheel = dependency_wheel()
    image = runtime_image()

    # Model verification owns its command input. It does not depend on the
    # separate Forge release-verification step to produce solidcraft.json.
    document = compile_commands(slug, wheel)
    write_commands(document, output / "solidcraft.json")

    verifier = ROOT / "examples" / slug / "verification" / "verify_model.py"
    if not verifier.is_file():
        raise RuntimeError(f"missing model verifier: {verifier}")

    subprocess.run(["docker", "pull", image], check=True)

    container_wheel = f"/forge-package/{wheel.name}"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "-e",
            f"PYTHONPATH={container_wheel}",
            "-e",
            "SOLIDCRAFT_GPU=cpu",
            "-v",
            f"{ROOT}:/workspace:ro",
            "-v",
            f"{output}:/output",
            "-v",
            f"{wheel.parent}:/forge-package:ro",
            "-w",
            "/workspace",
            image,
            "python",
            f"/workspace/examples/{slug}/verification/verify_model.py",
            "--input",
            "/output/solidcraft.json",
            "--output",
            "/output/model_verify",
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
