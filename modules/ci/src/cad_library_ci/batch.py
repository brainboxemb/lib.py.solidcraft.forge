"""Run each selected CAD runtime once in dependency order."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .config import ConfigError, mapping


def runtime_order(examples):
    roles = {role for e in examples for role in (e.runtime, e.verify_runtime)}
    dependencies = {role: set() for role in roles}
    for e in examples:
        if e.runtime != e.verify_runtime:
            dependencies[e.verify_runtime].add(e.runtime)
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


def _record(repo, runtimes, e):
    build_image = runtimes[e.runtime]["image"]
    return {
        "id": e.id, "builder": e.builder, "build_entry": e.build_entry,
        "verify_entry": e.verify_entry, "adapter": e.adapter,
        "source": "/repo/" + e.source.relative_to(repo).as_posix(),
        "definition": "/repo/" + e.definition.relative_to(repo).as_posix(),
        "preview_entry": e.preview_entry, "preview_adapter": e.preview_adapter,
        "engine_python": e.engine_python, "build_runtime": e.runtime,
        "build_image": build_image, "verify_runtime": e.verify_runtime,
    }


def run_batches(repo, project, modules, examples, output):
    if not examples:
        return
    runtimes = mapping(repo / "ci.yml").get("runtimes", {})
    by_id = {m.id: m for m in modules}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    for role in runtime_order(examples):
        runtime = runtimes.get(role, {})
        image = runtime.get("image")
        if not isinstance(image, str) or ":" not in image or image.endswith(":latest"):
            raise ConfigError(f"missing pinned runtime: {role}")
        build_rows = [e for e in examples if e.runtime == role]
        verify_rows = [e for e in examples if e.verify_runtime == role]
        active = tuple(dict.fromkeys([*build_rows, *verify_rows]))
        source_paths = {"/repo/modules/ci/src"}
        for e in active:
            for dependency in e.dependencies:
                if dependency == "cadlib":
                    source_paths.add("/repo/cadlib/src")
                else:
                    path = by_id[dependency].root.relative_to(repo)
                    source_paths.add(f"/repo/{path.as_posix()}/src")
        manifest = {
            "schema": 2, "runtime": role, "image": image,
            "build_examples": [_record(repo, runtimes, e) for e in build_rows],
            "verify_examples": [_record(repo, runtimes, e) for e in verify_rows],
        }
        with tempfile.TemporaryDirectory(prefix="cad-batch-") as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            command = ["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
                "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-e", "PYTHONPATH=" + ":".join(sorted(source_paths))]
            if runtime.get("version") is not None:
                command += ["-e", f"CAD_LIBRARY_RUNTIME_VERSION={runtime['version']}"]
            command += [
                "-v", f"{repo.resolve()}:/repo:ro",
                "-v", f"{output}:/output", "-v", f"{path}:/manifest.json:ro",
                "-w", "/repo", image, "python", "-m", "cad_library_ci.runtime",
                "--manifest", "/manifest.json", "--output", "/output",
            ]
            result = subprocess.run(command, check=False, timeout=1800)
            failed |= result.returncode != 0
    if failed:
        raise RuntimeError("one or more CAD runtime batches failed")
