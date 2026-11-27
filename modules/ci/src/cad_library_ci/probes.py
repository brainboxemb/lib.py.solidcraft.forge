"""Discover and select opt-in API probe owners."""
from dataclasses import dataclass
from pathlib import Path

from .config import ConfigError, _ID, mapping


@dataclass(frozen=True)
class ApiProbe:
    id: str
    root: Path
    builder: str
    source: Path
    runtime: str
    build_entry: str
    engine_python: str | None
    module_dependencies: tuple[str, ...]
    needs_cadlib: bool


def _owned_file(root, value):
    if not isinstance(value, str) or not value:
        raise ConfigError("probe source must be a non-empty string")
    rel = Path(value)
    path = root / rel
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or not path.is_file()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ConfigError(f"invalid probe source: {path}")
    return path


def _builder(by_module, builder, path):
    if not isinstance(builder, str) or builder not in by_module:
        raise ConfigError(f"unknown probe builder {builder!r}: {path}")
    data = mapping(by_module[builder].root / "ci.yml").get("builder")
    if not isinstance(data, dict):
        raise ConfigError(f"invalid builder capability: {builder}")
    entry, runtime = data.get("entrypoint"), data.get("runtime")
    if not isinstance(entry, str) or ":" not in entry:
        raise ConfigError(f"invalid builder entrypoint: {builder}")
    if not isinstance(runtime, str) or not _ID.fullmatch(runtime):
        raise ConfigError(f"invalid builder runtime: {builder}")
    needs = data.get("needs", [])
    if (
        not isinstance(needs, list)
        or not all(isinstance(item, str) and item in by_module for item in needs)
    ):
        raise ConfigError(f"invalid builder dependencies: {builder}")
    engine_python = data.get("python")
    if engine_python is not None:
        engine_path = Path(engine_python)
        if (
            not isinstance(engine_python, str)
            or not engine_path.is_absolute()
            or ".." in engine_path.parts
        ):
            raise ConfigError(f"invalid runtime interpreter for {builder}")
    return data, tuple(needs)


def discover_api_probes(repo, project, modules):
    root = repo / project.api_probes_root
    if not root.is_dir():
        return ()

    by_module = {module.id: module for module in modules}
    result, seen = [], set()
    for path in sorted(root.rglob("probe.yml")):
        data = mapping(path)
        if set(data) - {"schema", "id", "builder", "source", "needs"}:
            raise ConfigError(f"invalid probe keys: {path}")

        probe_id = data.get("id")
        if (
            not isinstance(probe_id, str)
            or not _ID.fullmatch(probe_id)
            or probe_id in seen
        ):
            raise ConfigError(f"invalid or duplicate API probe: {path}")

        probe_root = path.parent
        builder = data.get("builder")
        capability, builder_needs = _builder(by_module, builder, path)

        raw_needs = data.get("needs", [])
        if not isinstance(raw_needs, list) or not all(
            isinstance(need, str) for need in raw_needs
        ):
            raise ConfigError(f"invalid probe needs: {path}")

        module_needs = []
        needs_cadlib = False
        for need in raw_needs:
            if need == "cadlib":
                needs_cadlib = True
            elif need in by_module:
                module_needs.append(need)
            else:
                raise ConfigError(f"unknown probe dependency {need!r}: {path}")

        module_dependencies = tuple(
            dict.fromkeys((builder, *builder_needs, *module_needs))
        )
        result.append(
            ApiProbe(
                probe_id,
                probe_root,
                builder,
                _owned_file(probe_root, data.get("source")),
                capability["runtime"],
                capability["entrypoint"],
                capability.get("python"),
                module_dependencies,
                needs_cadlib,
            )
        )
        seen.add(probe_id)

    return tuple(sorted(result, key=lambda probe: probe.id))


def select_api_probes(probes, explicit):
    if explicit is None:
        return probes
    by_id = {probe.id: probe for probe in probes}
    missing = set(explicit) - by_id.keys()
    if missing:
        raise ConfigError("unknown api_probes: " + ", ".join(sorted(missing)))
    return tuple(by_id[probe_id] for probe_id in explicit)
