"""Load stable configuration and branch-local selections."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
import yaml


class ConfigError(ValueError):
    pass


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ProjectConfig:
    stable_branch: str
    development_branch: str
    modules_root: Path
    models_root: Path
    api_probes_root: Path
    output_root: Path


@dataclass(frozen=True)
class BuildSelection:
    branch: str
    modules: tuple[str, ...] | None
    models: tuple[str, ...] | None
    api_probes: tuple[str, ...] | None = ()
    tasks: tuple[str, ...] = ("test",)
    library: bool = False


def full_selection(branch):
    # API probes are deliberately opt-in, even for full permanent builds.
    return BuildSelection(branch, None, None, (), library=True)


def mapping(path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ConfigError(f"invalid schema: {path}")
    return data


def _relative(value):
    if not isinstance(value, str) or not value:
        raise ConfigError("root must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError("root must remain inside repository")
    return path


def _ids(value, field):
    if value == "all":
        return None
    if isinstance(value, list) and all(isinstance(x, str) and _ID.fullmatch(x) for x in value):
        return tuple(dict.fromkeys(value))
    raise ConfigError(f"{field} must be all or a list of ids")


def load_project(repo):
    data = mapping(repo / "ci.yml")
    branches, roots = data.get("branches"), data.get("roots")
    if not isinstance(branches, dict) or not isinstance(roots, dict):
        raise ConfigError("branches and roots must be mappings")
    stable, dev = branches.get("stable"), branches.get("development")
    if not all(isinstance(x, str) and x for x in (stable, dev)) or stable == dev:
        raise ConfigError("invalid source branches")
    return ProjectConfig(
        stable,
        dev,
        _relative(roots.get("modules")),
        _relative(roots.get("models")),
        _relative(roots.get("api_probes")),
        _relative(roots.get("output")),
    )


def load_build(repo, branch):
    path = repo / "build.yml"
    if not path.is_file():
        return None
    data = mapping(path)
    if data.get("branch") != branch:
        return None
    if data.get("tasks") != ["test"]:
        raise ConfigError("baseline supports only task test")
    library = data.get("library", False)
    if type(library) is not bool:
        raise ConfigError("library must be a boolean")
    return BuildSelection(
        branch,
        _ids(data.get("modules"), "modules"),
        _ids(data.get("models"), "models"),
        _ids(data.get("api_probes", []), "api_probes"),
        library=library,
    )


def current_branch(repo):
    for key in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        if os.environ.get(key, "").strip():
            return os.environ[key].strip()
    branch = subprocess.check_output(
        ["git", "-C", str(repo), "branch", "--show-current"], text=True
    ).strip()
    if not branch:
        raise ConfigError("cannot determine branch")
    return branch
