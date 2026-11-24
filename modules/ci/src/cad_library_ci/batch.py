"""Run each required CAD runtime once for selected model implementations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .config import ConfigError, mapping


def runtime_order(models):
    roles = {
        role
        for model in models
        for impl in model.implementations
        for role in (impl.runtime, model.verify_runtime)
    }
    dependencies = {role: set() for role in roles}
    for model in models:
        for impl in model.implementations:
            if impl.runtime != model.verify_runtime:
                dependencies[model.verify_runtime].add(impl.runtime)
    ordered = []
    while dependencies:
        ready = sorted(role for role, needs in dependencies.items() if not needs)
        if not ready:
            raise ConfigError("runtime dependency cycle")
        for role in ready:
            ordered.append(role)
            dependencies.pop(role)
        for needs in dependencies.values():
            needs.difference_update(ready)
    return tuple(ordered)


def _record(repo, runtimes, model, impl):
    return {
        "task_id": f"{model.id}--{impl.id}",
        "owner": model.id,
        "implementation": impl.id,
        "builder": impl.builder,
        "build_entry": impl.build_entry,
        "verify_entry": model.verify_entry,
        "adapter": model.adapter,
        "source": "/repo/" + impl.source.relative_to(repo).as_posix(),
        "definition": "/repo/" + model.definition.relative_to(repo).as_posix(),
        "preview_entry": impl.preview_entry,
        "preview_adapter": impl.preview_adapter,
        "engine_python": impl.engine_python,
        "build_runtime": impl.runtime,
        "build_image": runtimes[impl.runtime]["image"],
        "verify_runtime": model.verify_runtime,
    }


def _aggregate_model(output, model):
    root = output / "models" / model.id
    results = {}
    passed = True
    for impl in model.implementations:
        path = root / impl.id / "result.json"
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            result = {
                "id": f"{model.id}:{impl.id}",
                "owner": model.id,
                "implementation": impl.id,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
        results[impl.id] = result
        passed &= result.get("status") == "pass"

    summary = {
        "schema": 1,
        "id": model.id,
        "primary": model.primary,
        "status": "pass" if passed else "fail",
        "implementations": {
            impl_id: {
                "status": result.get("status"),
                "builder": result.get("builder"),
                "build_status": result.get("build_status"),
                "verification_status": result.get("verification_status"),
                "preview_status": result.get("preview_status"),
            }
            for impl_id, result in results.items()
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "result.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    primary = root / model.primary
    if passed:
        for name in ("model.stl", "model.png", "preview.json"):
            source = primary / name
            if source.is_file():
                shutil.copy2(source, root / name)
        report = primary / "verification" / "verification.json"
        if report.is_file():
            target = root / "verification" / "verification.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(report, target)
    return passed


def run_batches(repo, project, modules, models, output):
    if not models:
        return
    runtimes = mapping(repo / "ci.yml").get("runtimes", {})
    by_id = {m.id: m for m in modules}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed = False

    for role in runtime_order(models):
        runtime = runtimes.get(role, {})
        image = runtime.get("image")
        if not isinstance(image, str) or ":" not in image or image.endswith(":latest"):
            raise ConfigError(f"missing pinned runtime: {role}")

        build_pairs = [
            (model, impl)
            for model in models
            for impl in model.implementations
            if impl.runtime == role
        ]
        verify_pairs = [
            (model, impl)
            for model in models
            for impl in model.implementations
            if model.verify_runtime == role
        ]
        active_models = {model.id: model for model, _ in (*build_pairs, *verify_pairs)}
        source_paths = {"/repo/modules/ci/src"}
        for model in active_models.values():
            if model.needs_cadlib:
                source_paths.add("/repo/cadlib/src")
            for dependency in model.module_dependencies:
                path = by_id[dependency].root.relative_to(repo)
                source_paths.add(f"/repo/{path.as_posix()}/src")

        manifest = {
            "schema": 3,
            "runtime": role,
            "image": image,
            "build_items": [
                _record(repo, runtimes, model, impl)
                for model, impl in build_pairs
            ],
            "verify_items": [
                _record(repo, runtimes, model, impl)
                for model, impl in verify_pairs
            ],
        }

        with tempfile.TemporaryDirectory(prefix="cad-batch-") as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            command = [
                "docker", "run", "--rm",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "-e", "HOME=/tmp",
                "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-e", "PYTHONPATH=" + ":".join(sorted(source_paths)),
            ]
            if runtime.get("version") is not None:
                command += [
                    "-e",
                    f"CAD_LIBRARY_RUNTIME_VERSION={runtime['version']}",
                ]
            command += [
                "-v", f"{repo.resolve()}:/repo:ro",
                "-v", f"{output}:/output",
                "-v", f"{path}:/manifest.json:ro",
                "-w", "/repo",
                image,
                "python", "-m", "cad_library_ci.runtime",
                "--manifest", "/manifest.json",
                "--output", "/output",
            ]
            result = subprocess.run(command, check=False, timeout=1800)
            failed |= result.returncode != 0

    for model in models:
        failed |= not _aggregate_model(output, model)
    if failed:
        raise RuntimeError("one or more CAD runtime batches failed")
