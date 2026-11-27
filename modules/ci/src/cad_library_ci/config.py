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
    docs_only_prefixes: tuple[str, ...] = ()
    docs_only_modules: tuple[str, ...] = ()
    reuse_pr_branches: tuple[str, ...] = ()


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


def _prefixes(value, field):
    if value is None:
        return ()
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{field} must be a non-empty list of repository prefixes")
    result = []
    for item in value:
        if not isinstance(item, str) or not item or item.startswith("/"):
            raise ConfigError(f"{field} must contain relative repository prefixes")
        path = Path(item.rstrip("/"))
        if not path.parts or ".." in path.parts:
            raise ConfigError(f"{field} must remain inside repository")
        normalized = item.replace("\\", "/")
        if normalized not in result:
            result.append(normalized)
    return tuple(result)


def _branch_list(value, field):
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ConfigError(f"{field} must be a list of branch names")
    return tuple(dict.fromkeys(value))


def load_project(repo):
    data = mapping(repo / "ci.yml")
    branches, roots = data.get("branches"), data.get("roots")
    if not isinstance(branches, dict) or not isinstance(roots, dict):
        raise ConfigError("branches and roots must be mappings")
    stable, dev = branches.get("stable"), branches.get("development")
    if not all(isinstance(x, str) and x for x in (stable, dev)) or stable == dev:
        raise ConfigError("invalid source branches")

    qualification = data.get("qualification", {})
    if not isinstance(qualification, dict):
        raise ConfigError("qualification must be a mapping")
    pull_requests = qualification.get("pull_requests", {})
    permanent = qualification.get("permanent", {})
    if not isinstance(pull_requests, dict) or not isinstance(permanent, dict):
        raise ConfigError("qualification pull_requests/permanent must be mappings")

    docs_only = pull_requests.get("docs_only", {})
    reuse = permanent.get("reuse_pr_qualification", {})
    if not isinstance(docs_only, dict) or not isinstance(reuse, dict):
        raise ConfigError("qualification policies must be mappings")

    docs_modules = docs_only.get("modules", [])
    if not isinstance(docs_modules, list) or not all(
        isinstance(item, str) and _ID.fullmatch(item) for item in docs_modules
    ):
        raise ConfigError("docs-only modules must be a list of ids")

    reuse_branches = _branch_list(
        reuse.get("branches"),
        "reuse_pr_qualification branches",
    )
    allowed_branches = {stable, dev, "exp"}
    unexpected = sorted(set(reuse_branches) - allowed_branches)
    if unexpected:
        raise ConfigError(
            "reuse_pr_qualification branches must be permanent source branches: "
            + ", ".join(unexpected)
        )

    return ProjectConfig(
        stable,
        dev,
        _relative(roots.get("modules")),
        _relative(roots.get("models")),
        _relative(roots.get("api_probes")),
        _relative(roots.get("output")),
        _prefixes(docs_only.get("prefixes"), "docs-only prefixes"),
        tuple(dict.fromkeys(docs_modules)),
        reuse_branches,
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
