#!/usr/bin/env python3
"""Run one Forge example's model verification in the pinned SolidCraft runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def item_slug() -> str:
    """Return the example selected by CAD-CI."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required")
    return value


def output_root() -> Path:
    """Return this CAD-CI item's materialized output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def forge_package() -> Path:
    """Locate the exact Forge package produced by the direct dependency."""

    raw = os.environ.get("CAD_CI_DEPENDENCIES_JSON", "").strip()
    if not raw:
        raise RuntimeError("CAD_CI_DEPENDENCIES_JSON is required")
    dependencies = json.loads(raw)
    forge = dependencies.get("forge-tool")
    if not isinstance(forge, dict):
        raise RuntimeError("forge-tool dependency context is required")
    dependency_root = forge.get("output_root")
    if not isinstance(dependency_root, str) or not dependency_root:
        raise RuntimeError("forge-tool dependency output_root is required")

    wheels = tuple((Path(dependency_root) / "dist").glob("scpf-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one built Forge package, found {len(wheels)}"
        )
    return wheels[0].resolve()


def runtime_image() -> str:
    """Return the immutable runtime prepared before the CAD-CI run."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError(
            "FORGE_RUNTIME_IMAGE is required for model_verify"
        )
    return value


def main() -> int:
    """Pull the prepared runtime and execute the model-owned verification."""

    slug = item_slug()
    output = output_root()
    wheel = forge_package()
    image = runtime_image()
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
