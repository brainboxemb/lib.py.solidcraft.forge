#!/usr/bin/env python3
"""Run all active independent reference checks in one shared reference runtime."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

import yaml

from forge_example import dependency_output_root, dependency_wheel


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")
BATCH_DEPENDENCY = "reference-verification-batch"


def output_root() -> Path:
    """Return this CAD-CI item's output root."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    path = Path(value).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_image() -> str:
    """Return the immutable reference runtime image."""

    value = os.environ.get("REFERENCE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("REFERENCE_RUNTIME_IMAGE is required")
    return value


def source_sha() -> str:
    """Return the exact source commit under verification."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def processed_reference_slugs() -> tuple[str, ...]:
    """Return process:true models with the complete four-reference set."""

    slugs: list[str] = []
    for ci_path in sorted((ROOT / "examples").glob("*/ci.yml")):
        config = yaml.safe_load(ci_path.read_text(encoding="utf-8")) or {}
        if config.get("process", True) is False:
            continue
        model_root = ci_path.parent
        if not (model_root / "verification" / "reference_geometry.json").is_file():
            continue
        missing = [
            implementation
            for implementation in IMPLEMENTATIONS
            if not (model_root / implementation / "ci.yml").is_file()
            or not (model_root / implementation / "model.py").is_file()
        ]
        if missing:
            raise RuntimeError(
                f"{model_root.name}: incomplete reference set: "
                + ", ".join(missing)
            )
        slugs.append(model_root.name)

    if not slugs:
        raise RuntimeError("no processed reference models found")
    return tuple(slugs)


def run_batch() -> int:
    """Run the complete active reference set in one container."""

    output = output_root()
    references = output / "references"
    if references.exists():
        shutil.rmtree(references)
    references.mkdir(parents=True)

    wheel = dependency_wheel(
        "cad-verification-package",
        "brainboxemb_cad_verification_lib-*.whl",
    )
    image = runtime_image()
    slugs = processed_reference_slugs()

    subprocess.run(["docker", "pull", image], check=True)

    completed = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "-v",
            f"{ROOT}:/workspace:ro",
            "-v",
            f"{output}:/output",
            "-v",
            f"{wheel.parent}:/cad-verification:ro",
            "-w",
            "/workspace",
            "-e",
            (
                "PYTHONPATH="
                f"/cad-verification/{wheel.name}:"
                "/workspace/scpf:/workspace"
            ),
            image,
            "python",
            "/workspace/verification/reference_validation.py",
            "--cases",
            ",".join(slugs),
            "--implementations",
            "all",
            "--out",
            "/output/references",
            "--source-sha",
            source_sha(),
        ],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def reference_identity() -> tuple[str, str]:
    """Return model slug and implementation from the current item path."""

    value = os.environ.get("CAD_CI_ITEM_PATH", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM_PATH is required")

    path = Path(value)
    if path.is_absolute():
        repo_value = os.environ.get("CAD_CI_REPO", "").strip()
        if not repo_value:
            raise RuntimeError(
                "CAD_CI_REPO is required with an absolute CAD_CI_ITEM_PATH"
            )
        path = path.resolve().relative_to(Path(repo_value).resolve())

    parts = path.parts
    if len(parts) != 3 or parts[0] != "examples":
        raise RuntimeError(
            "reference item path must be examples/<model>/<implementation>"
        )
    if parts[2] not in IMPLEMENTATIONS:
        raise RuntimeError(f"unsupported reference implementation: {parts[2]}")
    return parts[1], parts[2]


def materialize_case() -> int:
    """Copy one reference result from the shared batch into its normal item."""

    slug, implementation = reference_identity()
    batch = dependency_output_root(BATCH_DEPENDENCY)
    batch_references = batch / "references"
    source = batch_references / slug / implementation
    if not source.is_dir():
        raise RuntimeError(f"missing reference batch result: {source}")

    destination = output_root() / "references"
    case_destination = destination / slug / implementation
    case_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, case_destination, dirs_exist_ok=True)

    report_path = batch_references / "verification.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    model = next(
        (
            row
            for row in report.get("models", [])
            if row.get("model") == slug
        ),
        None,
    )
    if model is None:
        raise RuntimeError(f"missing batch report row for {slug}")

    implementation_row = next(
        (
            row
            for row in model.get("implementations", [])
            if row.get("implementation") == implementation
        ),
        None,
    )
    if implementation_row is None:
        raise RuntimeError(
            f"missing batch report row for {slug}/{implementation}"
        )

    child_report = {
        "schema": report.get("schema", 1),
        "source_sha": report.get("source_sha"),
        "status": implementation_row.get("status", "fail"),
        "models": [
            {
                "model": slug,
                "status": implementation_row.get("status", "fail"),
                "implementations": [implementation_row],
            }
        ],
    }
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "verification.json").write_text(
        json.dumps(child_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return 0 if implementation_row.get("status") == "pass" else 1


def main() -> int:
    """Dispatch batch production or per-case materialization."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        nargs="?",
        choices=("batch", "materialize"),
        default="batch",
    )
    args = parser.parse_args()

    if args.operation == "materialize":
        return materialize_case()
    return run_batch()


if __name__ == "__main__":
    raise SystemExit(main())
