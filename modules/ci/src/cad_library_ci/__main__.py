"""Project CI entrypoint."""
import json
import os
import subprocess
from pathlib import Path
from urllib.error import URLError

from .batch import run_batches
from .config import (
    BuildSelection,
    ConfigError,
    current_branch,
    full_selection,
    load_build,
    load_project,
)
from .history import (
    changed_paths,
    changed_paths_from_base,
    changed_paths_from_parent,
    last_successful_dev_sha,
)
from .items import discover_modules, select
from .library import library_owner, build_wheel
from .models import discover_models, select_models
from .runner import execute, execute_model_tests
from .selection import changed_selection


RELEASE_BRANCH_PREFIX = "release/"
RELEASE_METADATA_PATHS = frozenset({
    "CHANGELOG.md",
    "cadlib/pyproject.toml",
})


def _is_full(plan):
    return plan.modules is None and plan.models is None and plan.library


def _release_plan(branch):
    return BuildSelection(branch, ("release",), (), library=True)


def _validated_release_paths(paths):
    if not paths:
        raise ConfigError("release branch has no release metadata changes")
    unexpected = sorted(set(paths) - RELEASE_METADATA_PATHS)
    if unexpected:
        raise ConfigError(
            "release branch changes non-release path(s): " + ", ".join(unexpected)
        )
    return tuple(paths)


def selection(repo, project, branch, modules):
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base = os.environ.get("GITHUB_BASE_REF", "")
    if (
        event == "pull_request"
        and branch == project.development_branch
        and base == project.stable_branch
    ):
        plan = full_selection(branch)
        return plan, None, True, False

    if (
        event == "pull_request"
        and base == project.stable_branch
        and branch.startswith(RELEASE_BRANCH_PREFIX)
    ):
        paths = _validated_release_paths(
            changed_paths_from_base(repo, base, "HEAD")
        )
        return _release_plan(branch), None, False, True

    if branch == project.stable_branch:
        if event == "push":
            target = os.environ.get("GITHUB_SHA", "").strip() or "HEAD"
            paths = changed_paths_from_parent(repo, target)
            if paths and set(paths) <= RELEASE_METADATA_PATHS:
                return _release_plan(branch), None, False, True
        plan = full_selection(branch)
        return plan, None, True, False
    if branch == project.development_branch:
        if event not in {"push", "workflow_dispatch"}:
            plan = full_selection(branch)
            return plan, None, True, False
        token, repository, target, run_id = (
            os.environ.get(key, "")
            for key in ("GH_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID")
        )
        if not (token and repository and target and run_id.isdigit()):
            plan = full_selection(branch)
            return plan, None, True, False
        try:
            baseline = last_successful_dev_sha(
                repository=repository,
                branch=branch,
                token=token,
                current_run_id=int(run_id),
                target_sha=target,
            )
        except (URLError, ValueError):
            plan = full_selection(branch)
            return plan, None, True, False
        paths = changed_paths(repo, baseline, target) if baseline else None
        if paths is None:
            plan = full_selection(branch)
            return plan, None, True, False
        plan = changed_selection(branch=branch, paths=paths, modules=modules)
        return plan, paths, _is_full(plan), False
    plan = load_build(repo, branch)
    if plan is None:
        plan = full_selection(branch)
        return plan, None, True, False
    return plan, None, _is_full(plan), False



def qualification_plan(
    *,
    models,
    selected,
    source_sha,
    full,
    library,
    release_only=False,
):
    return {
        "schema": 2,
        "source_sha": source_sha,
        "library": bool(library),
        "active": [model.id for model in models],
        "selected": [model.id for model in selected],
        "full": bool(full),
        "release_only": bool(release_only),
        "models": [
            {
                "id": model.id,
                "primary": model.primary,
                "implementations": [item.id for item in model.implementations],
                "purpose": list(model.purposes),
            }
            for model in models
        ],
    }


def main():
    repo = Path.cwd()
    project = load_project(repo)
    branch = current_branch(repo)
    modules = discover_modules(repo, project)
    plan, paths, full, release_only = selection(repo, project, branch, modules)

    chosen = select(modules, plan.modules)
    print("Selected modules:", ", ".join(item.id for item in chosen), flush=True)

    library = library_owner(repo)
    print("Selected library:", plan.library, flush=True)
    execute((*chosen, library) if plan.library else chosen)

    models = discover_models(repo, project, modules)
    if full:
        selected = models
    elif paths is None:
        selected = models if plan.models is None else select_models(models, explicit=plan.models)
    else:
        selected = select_models(
            models,
            paths=paths,
            selected_modules=tuple(m.id for m in chosen),
            library=plan.library,
        )
    print("Selected models:", ", ".join(model.id for model in selected), flush=True)
    execute_model_tests(
        repo,
        selected,
        library,
        dependencies_installed=plan.library,
    )

    output = repo / project.output_root / "qualification"
    output.mkdir(parents=True, exist_ok=True)
    if plan.library:
        build_wheel(library, output / "library")

    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    build_plan = qualification_plan(
        models=models,
        selected=selected,
        source_sha=source_sha,
        full=full,
        library=plan.library,
        release_only=release_only,
    )
    (output / "build-plan.json").write_text(
        json.dumps(build_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    run_batches(repo, project, modules, selected, output)


if __name__ == "__main__":
    main()
