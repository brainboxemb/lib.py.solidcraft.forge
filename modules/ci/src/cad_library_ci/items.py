"""Discover module-local ownership."""
from dataclasses import dataclass
from pathlib import Path
from .config import ConfigError, _ID, mapping

@dataclass(frozen=True)
class PythonModule:
    id: str
    root: Path
    impact: str
    watch: tuple[str, ...]

def discover_modules(repo, project):
    root = repo / project.modules_root
    result = {}
    for child in sorted(root.iterdir()):
        path = child / "ci.yml"
        if not child.is_dir() or not path.is_file():
            continue
        data = mapping(path)
        item_id = data.get("id")
        impact = data.get("impact", "self")
        extra = data.get("watch", [])
        if (data.get("kind") != "python" or not isinstance(item_id, str)
                or not _ID.fullmatch(item_id) or item_id in result
                or impact not in ("self", "full") or not isinstance(extra, list)
                or not all(isinstance(x, str) and x for x in extra)):
            raise ConfigError(f"invalid module config: {path}")
        result[item_id] = PythonModule(item_id, child, impact, (child.relative_to(repo).as_posix() + "/**", *extra))
    return tuple(result.values())

def select(items, ids):
    if ids is None:
        return items
    by_id = {item.id: item for item in items}
    missing = set(ids) - by_id.keys()
    if missing:
        raise ConfigError("unknown modules: " + ", ".join(sorted(missing)))
    return tuple(by_id[item_id] for item_id in ids)
