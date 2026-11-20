#!/usr/bin/env python3
"""Produce one Forge native model and delegate its checks to the library.

This is the staged declarative model-verification launcher. Host-side execution
consumes the `forge-package` and `cad-verification-package` CAD-CI
dependencies, compiles the selected Forge model with the exact Forge wheel and
starts the released SolidCraft runtime with the verification wheel mounted
read-only. Inside that runtime the launcher performs only
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
import time

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
    """Return the immutable released runtime selected by Forge CAD-CI."""

    value = os.environ.get("FORGE_RUNTIME_IMAGE", "").strip()
    if not value:
        raise RuntimeError("FORGE_RUNTIME_IMAGE is required for model_verify")
    return value


def verify_path(slug: str) -> Path:
    """Return one model-local declarative verification file."""

    return ROOT / "examples" / slug / "verification" / "verify.py"


def load_definition(path: Path):
    """Load one data-only model definition inside the released runtime."""

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

    inside_started = time.perf_counter()

    entry_ms = os.environ.get("FORGE_CONTAINER_ENTRY_MS", "").strip()
    if entry_ms:
        python_bootstrap_s = (
            time.time_ns() // 1_000_000 - int(entry_ms)
        ) / 1000.0
        print(
            f"FORGE TIMING python_bootstrap_s={python_bootstrap_s:.3f}",
            flush=True,
        )

    import_started = time.perf_counter()
    from cad_verification import run_solidcraft_verification
    print(
        "FORGE TIMING "
        f"cad_verification_import_s={time.perf_counter() - import_started:.3f}",
        flush=True,
    )

    path = verify_path(slug)
    if not path.is_file():
        raise RuntimeError(f"missing verification file: {path}")

    definition_started = time.perf_counter()
    definition = load_definition(path)
    print(
        "FORGE TIMING "
        f"definition_load_s={time.perf_counter() - definition_started:.3f}",
        flush=True,
    )

    native_started = time.perf_counter()
    model = produce_native_model(input_path.resolve(), output_dir.resolve())
    print(
        "FORGE TIMING "
        f"native_model_s={time.perf_counter() - native_started:.3f}",
        flush=True,
    )

    verification_started = time.perf_counter()
    report = run_solidcraft_verification(
        model,
        output_dir.resolve(),
        definition,
    )
    print(
        "FORGE TIMING "
        f"solidcraft_verification_s={time.perf_counter() - verification_started:.3f}",
        flush=True,
    )

    measurements = output_dir.resolve() / "baseline" / "measurements.json"
    visual_report = None
    visual_policy = path.parent / "visual.json"
    if visual_policy.is_file():
        from model_visual import run_visual_verification

        visual_started = time.perf_counter()
        visual_report = run_visual_verification(
            model,
            measurements,
            visual_policy,
            output_dir.resolve(),
        )
        print(
            "FORGE TIMING "
            f"visual_verification_s={time.perf_counter() - visual_started:.3f}",
            flush=True,
        )

    from model_visual import write_presentation_preview

    preview_started = time.perf_counter()
    write_presentation_preview(
        model,
        measurements,
        output_dir.resolve(),
    )
    print(
        "FORGE TIMING "
        f"presentation_preview_s={time.perf_counter() - preview_started:.3f}",
        flush=True,
    )

    print(
        "FORGE TIMING "
        f"inside_runtime_total_s={time.perf_counter() - inside_started:.3f}",
        flush=True,
    )
    print(f"{slug} model verification: {report['status']}", flush=True)
    if visual_report is not None:
        print(
            f"{slug} visual verification: {visual_report['status']}",
            flush=True,
        )

    passed = report["status"] == "pass"
    if visual_report is not None:
        passed = passed and visual_report["status"] == "pass"
    return 0 if passed else 1


def run_host() -> int:
    """Compile with the built Forge wheel and invoke the released runtime."""

    slug = item_slug()
    output = output_root()
    wheel = dependency_wheel()
    verification_wheel = dependency_wheel(
        "cad-verification-package",
        "brainboxemb_cad_verification_lib-*.whl",
    )
    image = runtime_image()

    if not verify_path(slug).is_file():
        raise RuntimeError(
            f"missing declarative verification file for {slug}"
        )

    compile_started = time.perf_counter()
    document = compile_commands(slug, wheel)
    write_commands(document, output / "solidcraft.json")
    print(
        "FORGE TIMING "
        f"compile_commands_s={time.perf_counter() - compile_started:.3f}",
        flush=True,
    )

    pull_started = time.perf_counter()
    subprocess.run(["docker", "pull", image], check=True)
    print(
        "FORGE TIMING "
        f"image_pull_s={time.perf_counter() - pull_started:.3f}",
        flush=True,
    )

    container_wheel = f"/forge-package/{wheel.name}"
    container_verification_wheel = (
        f"/cad-verification/{verification_wheel.name}"
    )
    container_started = time.perf_counter()
    container_launch_ms = time.time_ns() // 1_000_000
    entry_script = """entry_ms=$(date +%s%3N)
elapsed_ms=$((entry_ms - FORGE_CONTAINER_LAUNCH_MS))
printf 'FORGE TIMING container_start_s=%d.%03d\n' \
  "$((elapsed_ms / 1000))" "$((elapsed_ms % 1000))"
export FORGE_CONTAINER_ENTRY_MS="$entry_ms"
exec python "$@"
"""
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "-e",
            (
                "PYTHONPATH="
                f"{container_verification_wheel}:{container_wheel}"
            ),
            "-e",
            "SOLIDCRAFT_GPU=cpu",
            "-e",
            f"FORGE_CONTAINER_LAUNCH_MS={container_launch_ms}",
            "-v",
            f"{ROOT}:/workspace:ro",
            "-v",
            f"{output}:/output",
            "-v",
            f"{wheel.parent}:/forge-package:ro",
            "-v",
            f"{verification_wheel.parent}:/cad-verification:ro",
            "-w",
            "/workspace",
            image,
            "sh",
            "-c",
            entry_script,
            "forge-runtime",
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
    print(
        "FORGE TIMING "
        f"container_process_total_s={time.perf_counter() - container_started:.3f}",
        flush=True,
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
