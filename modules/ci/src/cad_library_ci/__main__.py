"""Project CI entrypoint."""
import os
import json
import subprocess
from pathlib import Path
from urllib.error import URLError
from .config import current_branch, full_selection, load_build, load_project, mapping, ConfigError
from .history import changed_paths, last_successful_dev_sha
from .items import discover_modules, select
from .runner import execute
from .selection import changed_selection
from .examples import discover_examples, select_examples
from .batch import run_batches
from .library import library_owner, build_wheel


def selection(repo, project, branch, modules):
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base = os.environ.get("GITHUB_BASE_REF", "")
    if branch == project.stable_branch or (event == "pull_request" and branch == project.development_branch and base == project.stable_branch):
        return full_selection(branch), None, True
    if branch == project.development_branch:
        if event not in {"push", "workflow_dispatch"}:
            return full_selection(branch), None, True
        token, repository, target, run_id = (os.environ.get(key, "") for key in ("GH_TOKEN", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID"))
        if not (token and repository and target and run_id.isdigit()):
            return full_selection(branch), None, True
        try:
            baseline = last_successful_dev_sha(repository=repository, branch=branch, token=token, current_run_id=int(run_id), target_sha=target)
        except (URLError, ValueError):
            return full_selection(branch), None, True
        paths = changed_paths(repo, baseline, target) if baseline else None
        if paths is None:
            return full_selection(branch), None, True
        plan = changed_selection(branch=branch, paths=paths, modules=modules)
        return plan, paths, plan.modules is None
    plan = load_build(repo, branch)
    return (plan, None, False) if plan else (full_selection(branch), None, True)


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
    examples = discover_examples(repo, modules)
    explicit = None
    if not full and paths is None:
        explicit = mapping(repo / "build.yml").get("examples", [])
        if explicit != "all" and (not isinstance(explicit, list) or not all(isinstance(i, str) for i in explicit)):
            raise ConfigError("examples must be all or a list of ids")
    selected = select_examples(examples, explicit=explicit, paths=paths, selected_modules=[m.id for m in chosen], full=full)
    print("Selected examples:", ", ".join(e.id for e in selected), flush=True)
    output = repo / project.output_root / "qualification"
    output.mkdir(parents=True, exist_ok=True)
    if plan.library:
        build_wheel(library, output / "library")
    (output / "build-plan.json").write_text(json.dumps({
        "schema": 1, "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "active": [e.id for e in examples], "selected": [e.id for e in selected], "full": full,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_batches(repo, project, modules, selected, output)


if __name__ == "__main__":
    main()
