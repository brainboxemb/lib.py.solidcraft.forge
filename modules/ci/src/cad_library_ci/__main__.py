"""Project CI entrypoint."""
import json
import os
import subprocess
from pathlib import Path
from urllib.error import URLError

from .batch import run_batches
from .config import current_branch, full_selection, load_build, load_project
from .history import changed_paths, last_successful_dev_sha
from .items import discover_modules, select
from .library import library_owner, build_wheel
from .models import discover_models, select_models
from .runner import execute
from .selection import changed_selection


def _is_full(plan):
    return plan.modules is None and plan.models is None and plan.library


def selection(repo, project, branch, modules):
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base = os.environ.get("GITHUB_BASE_REF", "")
    if branch == project.stable_branch or (
        event == "pull_request"
        and branch == project.development_branch
        and base == project.stable_branch
    ):
        plan = full_selection(branch)
        return plan, None, True
    if branch == project.development_branch:
        if event not in {"push", "workflow_dispatch"}:
            plan = full_selection(branch)
            return plan, None, True
        token, repository, target, run_id = (
            os.environ.get(key, "")
            for key in ("GH_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID")
        )
        if not (token and repository and target and run_id.isdigit()):
            plan = full_selection(branch)
            return plan, None, True
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
            return plan, None, True
        paths = changed_paths(repo, baseline, target) if baseline else None
        if paths is None:
            plan = full_selection(branch)
            return plan, None, True
        plan = changed_selection(branch=branch, paths=paths, modules=modules)
        return plan, paths, _is_full(plan)
    plan = load_build(repo, branch)
    if plan is None:
        plan = full_selection(branch)
        return plan, None, True
    return plan, None, _is_full(plan)


def main():
    repo = Path.cwd()
    project = load_project(repo)
    branch = current_branch(repo)
    modules = discover_modules(repo, project)
    plan, paths, full = selection(repo, project, branch, modules)

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

    output = repo / project.output_root / "qualification"
    output.mkdir(parents=True, exist_ok=True)
    if plan.library:
        build_wheel(library, output / "library")

    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    build_plan = {
        "schema": 2,
        "source_sha": source_sha,
        "active": [model.id for model in models],
        "selected": [model.id for model in selected],
        "full": full,
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
    (output / "build-plan.json").write_text(
        json.dumps(build_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    run_batches(repo, project, modules, selected, output)


if __name__ == "__main__":
    main()
