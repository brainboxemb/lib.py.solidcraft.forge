"""Run each required CAD runtime once for selected model implementations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .config import ConfigError, mapping


def _applicable_stages(model, implementation):
    return tuple(
        stage
        for stage in model.verifications
        if stage.applies_to(implementation.id)
    )


def runtime_order(models, probes=()):
    roles = set()
    dependencies = {}

    def require(role):
        roles.add(role)
        dependencies.setdefault(role, set())

    for model in models:
        for impl in model.implementations:
            require(impl.runtime)
            stages = _applicable_stages(model, impl)
            for stage in stages:
                require(stage.runtime)
                if stage.runtime != impl.runtime:
                    dependencies[stage.runtime].add(impl.runtime)

            if impl.preview_runtime:
                require(impl.preview_runtime)
                if impl.preview_runtime != impl.runtime:
                    dependencies[impl.preview_runtime].add(impl.runtime)
                for stage in stages:
                    if stage.runtime != impl.preview_runtime:
                        dependencies[impl.preview_runtime].add(stage.runtime)

    for probe in probes:
        require(probe.runtime)

    ordered = []
    while dependencies:
        ready = sorted(
            role for role, needs in dependencies.items() if not needs
        )
        if not ready:
            raise ConfigError("runtime dependency cycle")
        for role in ready:
            ordered.append(role)
            dependencies.pop(role)
        for needs in dependencies.values():
            needs.difference_update(ready)
    return tuple(ordered)


def _build_record(repo, runtimes, model, impl):
    return {
        "task_id": f"{model.id}--{impl.id}",
        "owner": model.id,
        "implementation": impl.id,
        "builder": impl.builder,
        "build_entry": impl.build_entry,
        "source": "/repo/" + impl.source.relative_to(repo).as_posix(),
        "engine_python": impl.engine_python,
        "build_runtime": impl.runtime,
        "build_image": runtimes[impl.runtime]["image"],
    }


def _probe_build_record(repo, runtimes, probe):
    return {
        "task_id": f"api-probe--{probe.id}",
        "owner": probe.id,
        "output_root": "api-probes",
        "implementation": "probe",
        "builder": probe.builder,
        "build_entry": probe.build_entry,
        "source": "/repo/" + probe.source.relative_to(repo).as_posix(),
        "engine_python": probe.engine_python,
        "build_runtime": probe.runtime,
        "build_image": runtimes[probe.runtime]["image"],
    }


def _verify_record(repo, runtimes, model, impl, stage):
    return {
        "task_id": f"{model.id}--{impl.id}",
        "owner": model.id,
        "implementation": impl.id,
        "builder": impl.builder,
        "stage_id": stage.id,
        "verify_entry": stage.entrypoint,
        "adapter": stage.adapter,
        "artifact": stage.artifact.as_posix(),
        "definition": "/repo/" + stage.definition.relative_to(repo).as_posix(),
        "build_image": runtimes[impl.runtime]["image"],
        "verify_runtime": stage.runtime,
    }


def _preview_record(model, impl):
    return {
        "task_id": f"{model.id}--{impl.id}",
        "owner": model.id,
        "implementation": impl.id,
        "preview_entry": impl.preview_entry,
        "preview_adapter": impl.preview_adapter,
        "artifact": "model.stl",
        "required_stages": [
            stage.id
            for stage in _applicable_stages(model, impl)
        ],
    }


def _load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            **fallback,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _aggregate_implementation(output, model, impl):
    root = output / "models" / model.id / impl.id
    build = _load_json(
        root / "build.json",
        {
            "id": f"{model.id}--{impl.id}",
            "owner": model.id,
            "implementation": impl.id,
            "builder": impl.builder,
            "build_status": "error",
        },
    )

    stage_results = {}
    for stage in _applicable_stages(model, impl):
        stage_results[stage.id] = _load_json(
            root / "verification" / stage.id / "stage-result.json",
            {
                "id": f"{model.id}--{impl.id}",
                "owner": model.id,
                "implementation": impl.id,
                "stage_id": stage.id,
            },
        )

    stage_statuses = [
        result.get("status")
        for result in stage_results.values()
    ]
    if stage_statuses and all(status == "pass" for status in stage_statuses):
        verification_status = "pass"
    elif any(status == "fail" for status in stage_statuses):
        verification_status = "fail"
    else:
        verification_status = "error"

    preview_status = None
    if impl.preview_entry:
        preview = _load_json(
            root / "preview-result.json",
            {
                "id": f"{model.id}--{impl.id}",
                "owner": model.id,
                "implementation": impl.id,
            },
        )
        preview_status = preview.get("status")

    status = (
        "pass"
        if build.get("build_status") == "pass"
        and verification_status == "pass"
        and (preview_status in {None, "pass"})
        else "fail"
    )

    result = {
        "schema": 2,
        "id": f"{model.id}--{impl.id}",
        "owner": model.id,
        "implementation": impl.id,
        "builder": impl.builder,
        "runtime": build.get("runtime"),
        "build_status": build.get("build_status"),
        "verification_status": verification_status,
        "verification_stages": {
            stage_id: {
                "status": stage_result.get("status"),
                "runtime": stage_result.get("verification_runtime"),
                "adapter": stage_result.get("adapter"),
            }
            for stage_id, stage_result in stage_results.items()
        },
        "preview_status": preview_status,
        "status": status,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    preferred = "geometry" if "geometry" in stage_results else next(iter(stage_results), None)
    if preferred:
        source = root / "verification" / preferred / "verification.json"
        if source.is_file():
            target = root / "verification" / "verification.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return result


def _aggregate_model(output, model):
    root = output / "models" / model.id
    results = {
        impl.id: _aggregate_implementation(output, model, impl)
        for impl in model.implementations
    }
    passed = all(result.get("status") == "pass" for result in results.values())

    summary = {
        "schema": 2,
        "id": model.id,
        "primary": model.primary,
        "status": "pass" if passed else "fail",
        "implementations": {
            impl_id: {
                "status": result.get("status"),
                "builder": result.get("builder"),
                "build_status": result.get("build_status"),
                "verification_status": result.get("verification_status"),
                "verification_stages": result.get("verification_stages"),
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
        for name in (
            "model.stl",
            "model.png",
            "model.sc",
            "model.step",
            "preview.json",
            "solidcraft.json",
        ):
            source = primary / name
            if source.is_file():
                shutil.copy2(source, root / name)
        report = primary / "verification" / "verification.json"
        if report.is_file():
            target = root / "verification" / "verification.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(report, target)
    return passed


def _aggregate_probe(output, probe):
    root = output / "api-probes" / probe.id
    implementation = root / "probe"
    build = _load_json(
        implementation / "build.json",
        {
            "id": f"api-probe--{probe.id}",
            "owner": probe.id,
            "implementation": "probe",
            "builder": probe.builder,
            "build_status": "error",
        },
    )
    passed = build.get("build_status") == "pass"
    result = {
        "schema": 1,
        "id": probe.id,
        "builder": probe.builder,
        "runtime": build.get("runtime"),
        "build_status": build.get("build_status"),
        "status": "pass" if passed else "fail",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if passed and implementation.is_dir():
        for source in implementation.iterdir():
            if source.name == "build.json":
                continue
            target = root / source.name
            if target.exists():
                shutil.rmtree(target) if target.is_dir() else target.unlink()
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
    return passed


def run_batches(repo, project, modules, models, output, *, probes=()):
    if not models and not probes:
        return

    runtimes = mapping(repo / "ci.yml").get("runtimes", {})
    by_id = {module.id: module for module in modules}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed = False

    for role in runtime_order(models, probes):
        runtime = runtimes.get(role, {})
        image = runtime.get("image")
        if (
            not isinstance(image, str)
            or ":" not in image
            or image.endswith(":latest")
        ):
            raise ConfigError(f"missing pinned runtime: {role}")

        build_pairs = [
            (model, impl)
            for model in models
            for impl in model.implementations
            if impl.runtime == role
        ]
        probe_builds = [
            probe
            for probe in probes
            if probe.runtime == role
        ]
        verify_rows = [
            (model, impl, stage)
            for model in models
            for impl in model.implementations
            for stage in _applicable_stages(model, impl)
            if stage.runtime == role
        ]
        preview_pairs = [
            (model, impl)
            for model in models
            for impl in model.implementations
            if impl.preview_entry and impl.preview_runtime == role
        ]

        active_models = {
            model.id: model
            for model, _ in (*build_pairs, *preview_pairs)
        }
        active_models.update(
            {model.id: model for model, _, _ in verify_rows}
        )

        source_paths = {"/repo/modules/ci/src"}
        for model in active_models.values():
            if model.needs_cadlib:
                source_paths.add("/repo/cadlib/src")
            for dependency in model.module_dependencies:
                path = by_id[dependency].root.relative_to(repo)
                source_paths.add(f"/repo/{path.as_posix()}/src")

        for probe in probe_builds:
            if probe.needs_cadlib:
                source_paths.add("/repo/cadlib/src")
            for dependency in probe.module_dependencies:
                path = by_id[dependency].root.relative_to(repo)
                source_paths.add(f"/repo/{path.as_posix()}/src")

        manifest = {
            "schema": 4,
            "runtime": role,
            "image": image,
            "build_items": [
                *[
                    _build_record(repo, runtimes, model, impl)
                    for model, impl in build_pairs
                ],
                *[
                    _probe_build_record(repo, runtimes, probe)
                    for probe in probe_builds
                ],
            ],
            "verify_items": [
                _verify_record(repo, runtimes, model, impl, stage)
                for model, impl, stage in verify_rows
            ],
            "preview_items": [
                _preview_record(model, impl)
                for model, impl in preview_pairs
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
    for probe in probes:
        failed |= not _aggregate_probe(output, probe)

    if failed:
        raise RuntimeError("one or more CAD runtime batches failed")
