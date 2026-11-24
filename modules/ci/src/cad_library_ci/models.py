"""Physical model ownership with model-local engine implementations."""
from dataclasses import dataclass
from pathlib import Path
from .config import ConfigError, _ID, mapping


_ALLOWED_PURPOSES = {"example", "verification"}


@dataclass(frozen=True)
class VerificationStage:
    id: str
    module: str
    adapter: str
    definition: Path
    artifact: Path
    runtime: str
    entrypoint: str
    implementations: tuple[str, ...] | None

    def applies_to(self, implementation_id: str) -> bool:
        return self.implementations is None or implementation_id in self.implementations


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
    preview_runtime: str | None
    module_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class Model:
    id: str
    root: Path
    implementations: tuple[Implementation, ...]
    primary: str
    verifications: tuple[VerificationStage, ...]
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
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or not path.is_file()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ConfigError(f"invalid model file: {path}")
    return path


def _generated_path(value, field, path):
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{field} must be a non-empty relative path: {path}")
    result = Path(value)
    if result.is_absolute() or ".." in result.parts:
        raise ConfigError(f"{field} must remain inside implementation output: {path}")
    return result


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


def _verifier_capability(modules, item_id, adapter):
    if item_id not in modules:
        raise ConfigError(f"unknown module: {item_id}")
    data = mapping(modules[item_id].root / "ci.yml").get("verifier")
    if not isinstance(data, dict):
        raise ConfigError(f"invalid verifier capability: {item_id}")

    adapters = data.get("adapters")
    if adapters is None:
        spec = data
    else:
        if not isinstance(adapters, dict):
            raise ConfigError(f"verifier.adapters must be a mapping: {item_id}")
        spec = adapters.get(adapter)
        if not isinstance(spec, dict):
            raise ConfigError(
                f"verifier {item_id} does not support adapter {adapter!r}"
            )

    entry, runtime = spec.get("entrypoint"), spec.get("runtime")
    if not isinstance(entry, str) or ":" not in entry:
        raise ConfigError(f"invalid verifier entrypoint: {item_id}:{adapter}")
    if not isinstance(runtime, str) or not _ID.fullmatch(runtime):
        raise ConfigError(f"invalid verifier runtime: {item_id}:{adapter}")
    return spec


def _group_priorities(root):
    groups = {}
    for path in sorted(root.rglob("ci.yml")):
        data = mapping(path)
        if data.get("kind") != "group":
            continue
        if set(data) != {"schema", "kind", "priority"}:
            raise ConfigError(
                f"group config may contain only schema, kind and priority: {path}"
            )
        priority = data.get("priority")
        if type(priority) is not int or priority < 0:
            raise ConfigError(
                f"group priority must be a non-negative integer: {path}"
            )
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
    if (
        not isinstance(values, list)
        or not values
        or not all(
            isinstance(value, str) and value in _ALLOWED_PURPOSES
            for value in values
        )
    ):
        raise ConfigError(
            f"model.yml purpose must contain example and/or verification: {model_root}"
        )
    if len(set(values)) != len(values):
        raise ConfigError(f"model.yml purpose must be unique: {model_root}")
    return tuple(values)


def _validate_dependencies(models):
    by_id = {model.id: model for model in models}
    for model in models:
        if model.id in model.dependencies:
            raise ConfigError(f"model cannot depend on itself: {model.id}")
        unknown = set(model.dependencies) - by_id.keys()
        if unknown:
            raise ConfigError(
                f"unknown model dependency for {model.id}: {sorted(unknown)[0]}"
            )

    visiting, visited = set(), set()

    def visit(model_id, trail):
        if model_id in visited:
            return
        if model_id in visiting:
            raise ConfigError(
                "cyclic model dependency: " + " -> ".join((*trail, model_id))
            )
        visiting.add(model_id)
        for dependency in by_id[model_id].dependencies:
            visit(dependency, (*trail, model_id))
        visiting.remove(model_id)
        visited.add(model_id)

    for model in models:
        visit(model.id, ())


def _verification_stages(data, model_root, by_module, implementation_ids, path):
    legacy = data.get("verification")
    raw = data.get("verifications")
    if legacy is not None and raw is not None:
        raise ConfigError(f"verification and verifications are mutually exclusive: {path}")

    if raw is None:
        if not isinstance(legacy, dict):
            raise ConfigError(f"model requires verification capability: {path}")
        raw = [{
            "id": "verification",
            "module": legacy.get("module"),
            "adapter": legacy.get("adapter"),
            "definition": legacy.get("definition"),
            "artifact": "model.stl",
        }]

    if not isinstance(raw, list) or not raw:
        raise ConfigError(f"verifications must be a non-empty list: {path}")

    stages = []
    stage_ids = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) - {
            "id", "module", "adapter", "definition", "artifact", "implementations"
        }:
            raise ConfigError(f"invalid verifications[{index}]: {path}")

        stage_id = item.get("id")
        module = item.get("module")
        adapter = item.get("adapter")
        if (
            not isinstance(stage_id, str)
            or not _ID.fullmatch(stage_id)
            or stage_id in stage_ids
        ):
            raise ConfigError(f"invalid or duplicate verification id: {path}")
        if not isinstance(module, str) or not isinstance(adapter, str):
            raise ConfigError(f"verification module and adapter are required: {path}")

        capability = _verifier_capability(by_module, module, adapter)
        implementations = item.get("implementations")
        if implementations is not None:
            if (
                not isinstance(implementations, list)
                or not implementations
                or not all(isinstance(value, str) for value in implementations)
                or len(set(implementations)) != len(implementations)
            ):
                raise ConfigError(
                    f"verification implementations must be a unique non-empty list: {path}"
                )
            unknown = set(implementations) - implementation_ids
            if unknown:
                raise ConfigError(
                    f"verification {stage_id} names unknown implementation: {sorted(unknown)[0]}"
                )
            implementation_filter = tuple(implementations)
        else:
            implementation_filter = None

        stages.append(
            VerificationStage(
                stage_id,
                module,
                adapter,
                _owned_file(model_root, item.get("definition")),
                _generated_path(item.get("artifact"), "verification artifact", path),
                capability["runtime"],
                capability["entrypoint"],
                implementation_filter,
            )
        )
        stage_ids.add(stage_id)

    for impl_id in implementation_ids:
        if not any(stage.applies_to(impl_id) for stage in stages):
            raise ConfigError(
                f"implementation {impl_id} has no verification stage: {path}"
            )
    return tuple(stages)


def discover_models(repo, project, modules):
    by_module = {module.id: module for module in modules}
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
        if (
            not isinstance(model_id, str)
            or not _ID.fullmatch(model_id)
            or model_id in seen
        ):
            raise ConfigError(f"invalid or duplicate model owner: {path}")
        model_root = path.parent

        preview = data.get("preview")
        preview_entry = preview_adapter = preview_module = preview_runtime = None
        if preview is not None:
            if (
                not isinstance(preview, dict)
                or not isinstance(preview.get("module"), str)
                or not isinstance(preview.get("adapter"), str)
            ):
                raise ConfigError(f"invalid preview capability: {path}")
            preview_module = preview["module"]
            capability = _capability(by_module, preview_module, "preview")
            preview_entry = capability["entrypoint"]
            preview_adapter = preview["adapter"]
            preview_runtime = capability["runtime"]

        raw_impl = data.get("implementations")
        if not isinstance(raw_impl, list) or not raw_impl:
            raise ConfigError(f"implementations must be a non-empty list: {path}")

        implementations, local_ids = [], set()
        model_modules = set()
        needs = data.get("needs", [])
        if not isinstance(needs, list) or not all(
            isinstance(need, str) for need in needs
        ):
            raise ConfigError(f"invalid model needs: {path}")
        needs_cadlib = "cadlib" in needs
        for need in needs:
            if need == "cadlib":
                continue
            if need not in by_module:
                raise ConfigError(f"unknown module dependency {need}: {path}")
            model_modules.add(need)
        if preview_module:
            model_modules.add(preview_module)

        for index, item in enumerate(raw_impl):
            if not isinstance(item, dict) or set(item) - {
                "id", "builder", "source", "preview"
            }:
                raise ConfigError(f"invalid implementations[{index}]: {path}")

            impl_id, builder = item.get("id"), item.get("builder")
            if (
                not isinstance(impl_id, str)
                or not _ID.fullmatch(impl_id)
                or impl_id in local_ids
            ):
                raise ConfigError(f"invalid or duplicate implementation id: {path}")
            if not isinstance(builder, str):
                raise ConfigError(f"implementation builder is required: {path}")

            capability = _capability(by_module, builder, "builder")
            builder_needs = capability.get("needs", [])
            if (
                not isinstance(builder_needs, list)
                or not all(
                    isinstance(need, str) and need in by_module
                    for need in builder_needs
                )
            ):
                raise ConfigError(f"invalid builder dependencies: {builder}")

            engine_python = capability.get("python")
            if engine_python is not None:
                engine_path = Path(engine_python)
                if (
                    not isinstance(engine_python, str)
                    or not engine_path.is_absolute()
                    or ".." in engine_path.parts
                ):
                    raise ConfigError(f"invalid runtime interpreter for {builder}")

            use_preview = item.get("preview", True)
            if type(use_preview) is not bool:
                raise ConfigError(
                    f"implementation preview must be boolean: {path}"
                )

            impl_modules = tuple(dict.fromkeys([builder, *builder_needs]))
            model_modules.update(impl_modules)
            implementations.append(
                Implementation(
                    impl_id,
                    builder,
                    _owned_file(model_root, item.get("source")),
                    capability["runtime"],
                    capability["entrypoint"],
                    engine_python,
                    preview_entry if use_preview else None,
                    preview_adapter if use_preview else None,
                    preview_runtime if use_preview else None,
                    impl_modules,
                )
            )
            local_ids.add(impl_id)

        primary = data.get("primary")
        if primary not in local_ids:
            raise ConfigError(f"primary must name an implementation: {path}")

        verifications = _verification_stages(
            data,
            model_root,
            by_module,
            local_ids,
            path,
        )
        model_modules.update(stage.module for stage in verifications)

        dependencies = data.get("dependencies", [])
        if (
            not isinstance(dependencies, list)
            or not all(
                isinstance(dependency, str) and _ID.fullmatch(dependency)
                for dependency in dependencies
            )
        ):
            raise ConfigError(f"invalid model dependencies: {path}")

        result.append(
            Model(
                model_id,
                model_root,
                tuple(implementations),
                primary,
                verifications,
                tuple(sorted(model_modules)),
                needs_cadlib,
                tuple(dict.fromkeys(dependencies)),
                _priority(model_root, root, groups),
                model_root.relative_to(repo).as_posix() + "/",
                _purposes(model_root),
            )
        )
        seen.add(model_id)

    _validate_dependencies(result)
    return tuple(sorted(result, key=lambda model: (model.priority, model.id)))


def expand_model_dependents(models, selected):
    chosen = set(selected)
    changed = True
    while changed:
        changed = False
        for model in models:
            if (
                model.id not in chosen
                and any(dependency in chosen for dependency in model.dependencies)
            ):
                chosen.add(model.id)
                changed = True
    return tuple(model for model in models if model.id in chosen)


def select_models(
    models,
    *,
    explicit=None,
    paths=None,
    selected_modules=(),
    library=False,
    full=False,
):
    if full or explicit is None and paths is None:
        return models if full else ()
    if explicit == "all":
        chosen = {model.id for model in models}
    elif explicit is not None:
        unknown = set(explicit) - {model.id for model in models}
        if unknown:
            raise ConfigError(f"unknown models: {sorted(unknown)}")
        chosen = set(explicit)
    else:
        module_ids = set(selected_modules)
        chosen = {
            model.id
            for model in models
            if module_ids.intersection(model.module_dependencies)
            or any(path.startswith(model.watch_prefix) for path in paths)
            or (library and model.needs_cadlib)
        }
    return expand_model_dependents(models, chosen)
