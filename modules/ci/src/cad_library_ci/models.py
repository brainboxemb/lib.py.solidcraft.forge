"""Physical model ownership with model-local engine implementations."""
from dataclasses import dataclass
from pathlib import Path
from .config import ConfigError, _ID, mapping


_ALLOWED_PURPOSES = {"example", "verification"}


@dataclass(frozen=True)
class Implementation:
    id: str
    builder: str
    source: Path
    runtime: str
    build_entry: str
    engine_python: str | None
    preview_entry: str | None
    preview_adapter: str | None
    module_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class Model:
    id: str
    root: Path
    implementations: tuple[Implementation, ...]
    primary: str
    verifier: str
    adapter: str
    definition: Path
    verify_runtime: str
    verify_entry: str
    module_dependencies: tuple[str, ...]
    needs_cadlib: bool
    dependencies: tuple[str, ...]
    priority: int
    watch_prefix: str
    purposes: tuple[str, ...]


def _owned_file(root, value):
    if not isinstance(value, str) or not value:
        raise ConfigError("model path must be a non-empty string")
    rel = Path(value)
    path = root / rel
    if rel.is_absolute() or ".." in rel.parts or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ConfigError(f"invalid model file: {path}")
    return path


def _capability(modules, item_id, kind):
    if item_id not in modules:
        raise ConfigError(f"unknown module: {item_id}")
    data = mapping(modules[item_id].root / "ci.yml").get(kind)
    if not isinstance(data, dict):
        raise ConfigError(f"invalid {kind} capability: {item_id}")
    entry, runtime = data.get("entrypoint"), data.get("runtime")
    if not isinstance(entry, str) or ":" not in entry:
        raise ConfigError(f"invalid {kind} entrypoint: {item_id}")
    if not isinstance(runtime, str) or not _ID.fullmatch(runtime):
        raise ConfigError(f"invalid {kind} runtime: {item_id}")
    return data


def _group_priorities(root):
    groups = {}
    for path in sorted(root.rglob("ci.yml")):
        data = mapping(path)
        if data.get("kind") != "group":
            continue
        if set(data) != {"schema", "kind", "priority"}:
            raise ConfigError(f"group config may contain only schema, kind and priority: {path}")
        priority = data.get("priority")
        if type(priority) is not int or priority < 0:
            raise ConfigError(f"group priority must be a non-negative integer: {path}")
        groups[path.parent] = priority
    return groups


def _priority(model_root, models_root, groups):
    current = model_root.parent
    while True:
        if current in groups:
            return groups[current]
        if current == models_root or models_root not in current.parents:
            break
        current = current.parent
    return groups.get(models_root, 1000)


def _purposes(model_root):
    metadata = mapping(model_root / "model.yml")
    raw = metadata.get("purpose")
    values = [raw] if isinstance(raw, str) else raw
    if not isinstance(values, list) or not values or not all(isinstance(v, str) and v in _ALLOWED_PURPOSES for v in values):
        raise ConfigError(f"model.yml purpose must contain example and/or verification: {model_root}")
    if len(set(values)) != len(values):
        raise ConfigError(f"model.yml purpose must be unique: {model_root}")
    return tuple(values)


def _validate_dependencies(models):
    by_id = {m.id: m for m in models}
    for model in models:
        if model.id in model.dependencies:
            raise ConfigError(f"model cannot depend on itself: {model.id}")
        unknown = set(model.dependencies) - by_id.keys()
        if unknown:
            raise ConfigError(f"unknown model dependency for {model.id}: {sorted(unknown)[0]}")
    visiting, visited = set(), set()
    def visit(model_id, trail):
        if model_id in visited:
            return
        if model_id in visiting:
            raise ConfigError("cyclic model dependency: " + " -> ".join((*trail, model_id)))
        visiting.add(model_id)
        for dependency in by_id[model_id].dependencies:
            visit(dependency, (*trail, model_id))
        visiting.remove(model_id)
        visited.add(model_id)
    for model in models:
        visit(model.id, ())


def discover_models(repo, project, modules):
    by_module = {m.id: m for m in modules}
    root = repo / project.models_root
    groups = _group_priorities(root)
    result, seen = [], set()
    if not root.is_dir():
        return ()
    for path in sorted(root.rglob("ci.yml")):
        data = mapping(path)
        if data.get("kind") == "group":
            continue
        process = data.get("process", True)
        if type(process) is not bool:
            raise ConfigError(f"process must be boolean: {path}")
        if not process:
            continue
        model_id = data.get("id")
        if not isinstance(model_id, str) or not _ID.fullmatch(model_id) or model_id in seen:
            raise ConfigError(f"invalid or duplicate model owner: {path}")
        model_root = path.parent
        verification = data.get("verification")
        if not isinstance(verification, dict):
            raise ConfigError(f"model requires verification capability: {path}")
        verifier = verification.get("module")
        adapter = verification.get("adapter")
        if not isinstance(verifier, str) or not isinstance(adapter, str):
            raise ConfigError(f"invalid verification capability: {path}")
        vc = _capability(by_module, verifier, "verifier")

        preview = data.get("preview")
        preview_entry = preview_adapter = preview_module = None
        preview_runtime = None
        if preview is not None:
            if not isinstance(preview, dict) or not isinstance(preview.get("module"), str) or not isinstance(preview.get("adapter"), str):
                raise ConfigError(f"invalid preview capability: {path}")
            preview_module = preview["module"]
            pc = _capability(by_module, preview_module, "preview")
            preview_entry, preview_adapter, preview_runtime = pc["entrypoint"], preview["adapter"], pc["runtime"]
            if preview_runtime != vc["runtime"]:
                raise ConfigError(f"preview runtime must match verifier runtime: {path}")

        raw_impl = data.get("implementations")
        if not isinstance(raw_impl, list) or not raw_impl:
            raise ConfigError(f"implementations must be a non-empty list: {path}")
        implementations, local_ids = [], set()
        model_modules = {verifier}
        needs = data.get("needs", [])
        if not isinstance(needs, list) or not all(isinstance(n, str) for n in needs):
            raise ConfigError(f"invalid model needs: {path}")
        needs_cadlib = "cadlib" in needs
        for need in needs:
            if need != "cadlib":
                if need not in by_module:
                    raise ConfigError(f"unknown module dependency {need}: {path}")
                model_modules.add(need)
        if preview_module:
            model_modules.add(preview_module)

        for index, item in enumerate(raw_impl):
            if not isinstance(item, dict) or set(item) - {"id", "builder", "source", "preview"}:
                raise ConfigError(f"invalid implementations[{index}]: {path}")
            impl_id, builder = item.get("id"), item.get("builder")
            if not isinstance(impl_id, str) or not _ID.fullmatch(impl_id) or impl_id in local_ids:
                raise ConfigError(f"invalid or duplicate implementation id: {path}")
            if not isinstance(builder, str):
                raise ConfigError(f"implementation builder is required: {path}")
            bc = _capability(by_module, builder, "builder")
            builder_needs = bc.get("needs", [])
            if not isinstance(builder_needs, list) or not all(isinstance(n, str) and n in by_module for n in builder_needs):
                raise ConfigError(f"invalid builder dependencies: {builder}")
            engine_python = bc.get("python")
            if engine_python is not None:
                engine_path = Path(engine_python)
                if not isinstance(engine_python, str) or not engine_path.is_absolute() or ".." in engine_path.parts:
                    raise ConfigError(f"invalid runtime interpreter for {builder}")
            use_preview = item.get("preview", True)
            if type(use_preview) is not bool:
                raise ConfigError(f"implementation preview must be boolean: {path}")
            impl_modules = tuple(dict.fromkeys([builder, *builder_needs]))
            model_modules.update(impl_modules)
            implementations.append(Implementation(
                impl_id,
                builder,
                _owned_file(model_root, item.get("source")),
                bc["runtime"],
                bc["entrypoint"],
                engine_python,
                preview_entry if use_preview else None,
                preview_adapter if use_preview else None,
                impl_modules,
            ))
            local_ids.add(impl_id)

        primary = data.get("primary")
        if primary not in local_ids:
            raise ConfigError(f"primary must name an implementation: {path}")
        dependencies = data.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(n, str) and _ID.fullmatch(n) for n in dependencies):
            raise ConfigError(f"invalid model dependencies: {path}")
        result.append(Model(
            model_id, model_root, tuple(implementations), primary,
            verifier, adapter, _owned_file(model_root, verification.get("definition")),
            vc["runtime"], vc["entrypoint"], tuple(sorted(model_modules)),
            needs_cadlib, tuple(dict.fromkeys(dependencies)),
            _priority(model_root, root, groups),
            model_root.relative_to(repo).as_posix() + "/",
            _purposes(model_root),
        ))
        seen.add(model_id)
    _validate_dependencies(result)
    return tuple(sorted(result, key=lambda m: (m.priority, m.id)))


def expand_model_dependents(models, selected):
    chosen = set(selected)
    changed = True
    while changed:
        changed = False
        for model in models:
            if model.id not in chosen and any(dep in chosen for dep in model.dependencies):
                chosen.add(model.id)
                changed = True
    return tuple(m for m in models if m.id in chosen)


def select_models(models, *, explicit=None, paths=None, selected_modules=(), library=False, full=False):
    if full or explicit is None and paths is None:
        return models if full else ()
    if explicit == "all":
        chosen = {m.id for m in models}
    elif explicit is not None:
        unknown = set(explicit) - {m.id for m in models}
        if unknown:
            raise ConfigError(f"unknown models: {sorted(unknown)}")
        chosen = set(explicit)
    else:
        module_ids = set(selected_modules)
        chosen = {
            m.id for m in models
            if module_ids.intersection(m.module_dependencies)
            or any(p.startswith(m.watch_prefix) for p in paths)
            or (library and m.needs_cadlib)
        }
    return expand_model_dependents(models, chosen)
