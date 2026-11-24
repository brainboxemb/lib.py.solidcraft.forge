"""Example ownership and engine-neutral runtime planning."""
from dataclasses import dataclass
from pathlib import Path
import re

from .config import ConfigError, mapping

_ID = re.compile(r"[a-z0-9][a-z0-9_-]*")
_ENTRY = re.compile(r"[a-zA-Z_][a-zA-Z0-9_.]*:[a-zA-Z_][a-zA-Z0-9_]*")


@dataclass(frozen=True)
class Example:
    id: str
    root: Path
    builder: str
    source: Path
    verifier: str
    adapter: str
    definition: Path
    runtime: str
    verify_runtime: str
    build_entry: str
    verify_entry: str
    dependencies: tuple[str, ...]
    watch_prefix: str
    preview_entry: str | None = None
    preview_adapter: str | None = None
    engine_python: str | None = None


def owned_file(root, value):
    if not isinstance(value, str) or not value:
        raise ConfigError("example path must be a string")
    path = root / value
    if Path(value).is_absolute() or ".." in Path(value).parts or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ConfigError(f"invalid example file: {path}")
    return path


def capability(modules, item_id, kind):
    if item_id not in modules:
        raise ConfigError(f"unknown module: {item_id}")
    data = mapping(modules[item_id].root / "ci.yml").get(kind)
    if not isinstance(data, dict) or not _ENTRY.fullmatch(str(data.get("entrypoint", ""))):
        raise ConfigError(f"invalid {kind} capability: {item_id}")
    runtime = data.get("runtime")
    if not isinstance(runtime, str) or not _ID.fullmatch(runtime):
        raise ConfigError(f"invalid {kind} runtime: {item_id}")
    return data


def discover_examples(repo, modules):
    by_id = {m.id: m for m in modules}
    root = repo / "examples"
    examples = []
    seen = set()
    if not root.is_dir():
        return ()
    for directory in sorted(root.iterdir()):
        path = directory / "ci.yml"
        if not path.is_file():
            continue
        data = mapping(path)
        item_id = data.get("id")
        if data.get("kind") != "example" or not isinstance(item_id, str) or not _ID.fullmatch(item_id) or item_id in seen:
            raise ConfigError(f"invalid example owner: {path}")
        builder = data.get("builder")
        v = data.get("verification")
        if not isinstance(builder, str) or not isinstance(v, dict) or not isinstance(v.get("module"), str) or not isinstance(v.get("adapter"), str):
            raise ConfigError(f"invalid example capabilities: {path}")
        b = capability(by_id, builder, "builder")
        verifier = v["module"]
        vc = capability(by_id, verifier, "verifier")
        runtime, verify_runtime = b["runtime"], vc["runtime"]
        engine_python = b.get("python")
        if engine_python is not None and (not isinstance(engine_python, str) or not Path(engine_python).is_absolute() or ".." in Path(engine_python).parts):
            raise ConfigError(f"invalid runtime interpreter for {builder}")
        needs = data.get("needs", [])
        if not isinstance(needs, list) or any(n != "cadlib" and n not in by_id for n in needs):
            raise ConfigError(f"invalid dependencies: {path}")
        builder_needs = b.get("needs", [])
        if not isinstance(builder_needs, list) or not all(isinstance(n, str) and n in by_id for n in builder_needs):
            raise ConfigError(f"invalid builder dependencies: {builder}")
        needs = [*needs, *builder_needs]
        preview_entry = preview_adapter = None
        if (preview := data.get("preview")) is not None:
            if not isinstance(preview, dict) or not isinstance(preview.get("module"), str) or not isinstance(preview.get("adapter"), str):
                raise ConfigError(f"invalid preview capability: {path}")
            pc = capability(by_id, preview["module"], "preview")
            if pc["runtime"] != verify_runtime:
                raise ConfigError("preview runtime must match verifier runtime")
            preview_entry = pc["entrypoint"]
            preview_adapter = preview["adapter"]
            needs = [*needs, preview["module"]]
        examples.append(Example(
            item_id, directory, builder, owned_file(directory, data.get("source")),
            verifier, v["adapter"], owned_file(directory, v.get("definition")),
            runtime, verify_runtime, b["entrypoint"], vc["entrypoint"],
            tuple(dict.fromkeys([builder, verifier, *needs])),
            directory.relative_to(repo).as_posix() + "/",
            preview_entry, preview_adapter, engine_python,
        ))
        seen.add(item_id)
    return tuple(examples)


def select_examples(examples, *, explicit=None, paths=None, selected_modules=(), full=False):
    if full or explicit == "all":
        return examples
    if explicit is not None:
        unknown = set(explicit) - {e.id for e in examples}
        if unknown:
            raise ConfigError(f"unknown examples: {sorted(unknown)}")
        return tuple(e for e in examples if e.id in explicit)
    if paths is None:
        return ()
    chosen = set(selected_modules)
    return tuple(e for e in examples if chosen.intersection(e.dependencies)
        or any(p.startswith(e.watch_prefix) for p in paths)
        or ("cadlib" in e.dependencies and any(p.startswith("cadlib/") for p in paths)))
