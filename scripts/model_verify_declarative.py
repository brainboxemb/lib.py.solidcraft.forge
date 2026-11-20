#!/usr/bin/env python3
"""Produce one Forge native model and delegate its checks to the library.

This is the staged declarative model-verification launcher. Host-side execution
compiles the selected Forge model with the exact built Forge wheel and starts
the pinned SolidCraft runtime. Inside that runtime the launcher performs only
the Forge-owned producer step: replay the compiled command document into the
initial native SolidCraft model. All checks, mutations and evidence are then
owned by released lib.py.cad.verfication.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
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
    """Return this CAD-CI model item's output directory."""

    value = os.environ.get("CAD_CI_OUTPUT", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_OUTPUT is required")
    return Path(value).resolve()


def runtime_image() -> str:
    """Return the immutable runtime configured for normal Forge CI."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("FORGE_RUNTIME_IMAGE is required for model_verify")
    return value


def verify_path(slug: str) -> Path:
    """Return one model-local declarative verification file."""

    return ROOT / "examples" / slug / "verification" / "verify.py"


def load_definition(path: Path):
    """Load one data-only model definition inside the pinned runtime."""

    namespace = runpy.run_path(str(path))
    definition = namespace.get("VERIFICATION")

    from cad_verification import SolidCraftVerification

    if not isinstance(definition, SolidCraftVerification):
        raise RuntimeError(
            f"verification file must export SolidCraftVerification: {path}"
        )
    return definition


def produce_native_model(input_path: Path, output_dir: Path) -> Path:
    """Replay Forge output into the initial editable SolidCraft model."""

    from scpf.headless import run_document

    value = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(
            f"Forge command document must contain one object: {input_path}"
        )

    native = output_dir / "native"
    native.mkdir(parents=True, exist_ok=True)
    model = native / "model.sc"

    run_document(
        value,
        save=model,
        export=native / "model.step",
        results_out=native / "results.json",
        replay_log_out=native / "replay-log.json",
        work_dir=native / "replay_work",
    )
    return model


def run_inside_runtime(
    slug: str,
    input_path: Path,
    output_dir: Path,
) -> int:
    """Produce the native model and hand all verification to the library."""

    from cad_verification import run_solidcraft_verification

    path = verify_path(slug)
    if not path.is_file():
        raise RuntimeError(f"missing verification file: {path}")

    definition = load_definition(path)
    model = produce_native_model(input_path.resolve(), output_dir.resolve())
    report = run_solidcraft_verification(
        model,
        output_dir.resolve(),
        definition,
    )
    print(f"{slug} model verification: {report['status']}")
    return 0 if report["status"] == "pass" else 1


def run_host() -> int:
    """Compile with the built Forge wheel and invoke the pinned runtime."""

    slug = item_slug()
    output = output_root()
    wheel = dependency_wheel()
    image = runtime_image()

    if not verify_path(slug).is_file():
        raise RuntimeError(
            f"missing declarative verification file for {slug}"
        )

    document = compile_commands(slug, wheel)
    write_commands(document, output / "solidcraft.json")

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
            "/workspace/scripts/model_verify_declarative.py",
            "--inside-runtime",
            "--slug",
            slug,
            "--input",
            "/output/solidcraft.json",
            "--output",
            "/output/model_verify",
        ],
        check=True,
    )
    return 0


def main() -> int:
    """Dispatch host-side CI work or the in-runtime Forge handoff."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside-runtime", action="store_true")
    parser.add_argument("--slug")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not args.inside_runtime:
        if args.slug is not None or args.input is not None or args.output is not None:
            parser.error("--slug/--input/--output require --inside-runtime")
        return run_host()

    if not args.slug or args.input is None or args.output is None:
        parser.error("--inside-runtime requires --slug, --input and --output")

    return run_inside_runtime(args.slug, args.input, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
