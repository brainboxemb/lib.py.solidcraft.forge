#!/usr/bin/env python3
"""Run declarative SolidCraft verification as one shared runtime batch."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback

import yaml

from forge_example import (
    compile_commands,
    dependency_output_root,
    dependency_wheel,
    write_commands,
)


ROOT = Path(__file__).resolve().parents[1]
BATCH_DEPENDENCY = "model-verification-batch"


def output_root() -> Path:
    """Return this CAD-CI item's output root."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    path = Path(value).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_image() -> str:
    """Return the immutable SolidCraft runtime image."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("FORGE_RUNTIME_IMAGE is required")
    return value


def source_sha() -> str:
    """Return the exact source commit under verification."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def processed_declarative_slugs() -> tuple[str, ...]:
    """Return process:true models that own declarative verification data."""

    slugs: list[str] = []
    for verify in sorted((ROOT / "examples").glob("*/verification/verify.py")):
        model_root = verify.parents[1]
        ci_path = model_root / "ci.yml"
        if not ci_path.is_file():
            continue
        config = yaml.safe_load(ci_path.read_text(encoding="utf-8")) or {}
        if config.get("process", True) is False:
            continue
        slugs.append(model_root.name)
    if not slugs:
        raise RuntimeError("no processed declarative models found")
    return tuple(slugs)


def write_manifest(batch_root: Path, wheel: Path) -> Path:
    """Compile every selected model and write one runtime manifest."""

    rows = []
    for slug in processed_declarative_slugs():
        case_root = batch_root / slug
        case_root.mkdir(parents=True, exist_ok=True)
        command_path = case_root / "solidcraft.json"
        write_commands(compile_commands(slug, wheel), command_path)
        rows.append(
            {
                "slug": slug,
                "input": f"/output/models/{slug}/solidcraft.json",
                "output": f"/output/models/{slug}/model_verify",
            }
        )

    manifest = batch_root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": 1,
                "source_sha": source_sha(),
                "models": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def run_host_batch() -> int:
    """Compile the case list, then verify it in one SolidCraft container."""

    output = output_root()
    batch_root = output / "models"
    if batch_root.exists():
        shutil.rmtree(batch_root)
    batch_root.mkdir(parents=True)

    forge_wheel = dependency_wheel("forge-package", "scpf-*.whl")
    verification_wheel = dependency_wheel(
        "cad-verification-package",
        "brainboxemb_cad_verification_lib-*.whl",
    )
    manifest = write_manifest(batch_root, forge_wheel)
    image = runtime_image()

    subprocess.run(["docker", "pull", image], check=True)

    container_forge_wheel = f"/forge-package/{forge_wheel.name}"
    container_verification_wheel = (
        f"/cad-verification/{verification_wheel.name}"
    )
    completed = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "-e",
            (
                "PYTHONPATH="
                f"{container_verification_wheel}:{container_forge_wheel}"
            ),
            "-e",
            "SOLIDCRAFT_GPU=cpu",
            "-v",
            f"{ROOT}:/workspace:ro",
            "-v",
            f"{output}:/output",
            "-v",
            f"{forge_wheel.parent}:/forge-package:ro",
            "-v",
            f"{verification_wheel.parent}:/cad-verification:ro",
            "-w",
            "/workspace",
            image,
            "python",
            "/workspace/scripts/model_verification_batch.py",
            "--inside-runtime",
            "--manifest",
            "/output/models/manifest.json",
        ],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def run_inside_runtime(manifest_path: Path) -> int:
    """Process every model, retaining failures until the complete list is done."""

    from model_verify_declarative import run_inside_runtime as verify_one

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("models")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("model verification batch manifest has no models")

    results = []
    failed = False
    for row in rows:
        slug = row["slug"]
        try:
            code = verify_one(
                slug,
                Path(row["input"]),
                Path(row["output"]),
            )
            status = "pass" if code == 0 else "fail"
            error = None
        except Exception as exc:  # keep later cases observable
            code = 1
            status = "error"
            error = "".join(
                traceback.format_exception_only(type(exc), exc)
            ).strip()
            print(f"{slug} model verification: error: {error}", flush=True)

        failed = failed or code != 0
        results.append(
            {
                "model": slug,
                "status": status,
                "error": error,
            }
        )

    report = {
        "schema": 1,
        "source_sha": manifest.get("source_sha"),
        "status": "fail" if failed else "pass",
        "models": results,
    }
    report_path = manifest_path.parent / "verification-batch.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = ", ".join(
        f"{row['model']}={row['status']}" for row in results
    )
    print(f"SolidCraft verification batch: {summary}", flush=True)
    return 1 if failed else 0


def materialize_case() -> int:
    """Copy this model's already-produced batch result to its normal output."""

    slug = os.environ.get("CAD_CI_ITEM", "").strip()
    if not slug:
        raise RuntimeError("CAD_CI_ITEM is required")

    batch = dependency_output_root(BATCH_DEPENDENCY)
    source = batch / "models" / slug
    if not source.is_dir():
        raise RuntimeError(f"missing model batch result: {source}")

    destination = output_root()
    command_source = source / "solidcraft.json"
    verify_source = source / "model_verify"
    if not command_source.is_file() or not verify_source.is_dir():
        raise RuntimeError(f"incomplete model batch result: {source}")

    shutil.copy2(command_source, destination / "solidcraft.json")
    shutil.copytree(
        verify_source,
        destination / "model_verify",
        dirs_exist_ok=True,
    )
    return 0


def main() -> int:
    """Dispatch batch production, in-runtime execution or case extraction."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        nargs="?",
        choices=("batch", "materialize"),
        default="batch",
    )
    parser.add_argument("--inside-runtime", action="store_true")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    if args.inside_runtime:
        if args.manifest is None:
            parser.error("--inside-runtime requires --manifest")
        return run_inside_runtime(args.manifest)

    if args.manifest is not None:
        parser.error("--manifest requires --inside-runtime")
    if args.operation == "materialize":
        return materialize_case()
    return run_host_batch()


if __name__ == "__main__":
    raise SystemExit(main())
