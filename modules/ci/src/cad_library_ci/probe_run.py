"""Run explicitly selected API probes without model/library qualification."""
import argparse
import json
from pathlib import Path
import subprocess

from .batch import run_batches
from .config import ConfigError, load_project
from .items import discover_modules
from .probes import discover_api_probes, select_api_probes


def _selection(value):
    value = value.strip()
    if value == "all":
        return None
    ids = tuple(dict.fromkeys(
        item.strip() for item in value.split(",") if item.strip()
    ))
    if not ids:
        raise ConfigError("--probes requires one or more ids, or all")
    return ids


def run(repo, output, probes):
    project = load_project(repo)
    modules = discover_modules(repo, project)
    available = discover_api_probes(repo, project, modules)
    selected = select_api_probes(available, _selection(probes))
    output.mkdir(parents=True, exist_ok=True)
    run_batches(repo, project, modules, (), output, probes=selected)
    source_sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    plan = {
        "schema": 1,
        "source_sha": source_sha,
        "available": [probe.id for probe in available],
        "selected": [probe.id for probe in selected],
    }
    (output / "api-probe-plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probes", required=True)
    args = parser.parse_args()
    run(args.repo.resolve(), args.output.resolve(), args.probes)


if __name__ == "__main__":
    main()
