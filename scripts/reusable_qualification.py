#!/usr/bin/env python3
"""Select reusable full qualification evidence for a site-only build.

This uses the same risk rules as PR verification. A previous successful full
qualification may be reused only when every change since that run remains at
the preflight level and no reference execution is required.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.preview_scope import (
    affected_cases,
    changed_paths,
    final_gate,
    reference_smoke_required,
)


ZERO_SHA = "0" * 40


def reusable_paths(paths: tuple[str, ...] | list[str]) -> bool:
    """Return whether existing qualified technical evidence is still valid."""
    try:
        cases = affected_cases(tuple(paths))
    except ValueError:
        return False
    return (
        final_gate(tuple(paths), cases) == "preflight"
        and not reference_smoke_required(tuple(paths))
    )


def normalize_base(base: str, head: str) -> str:
    if base and base != ZERO_SHA:
        return base
    completed = subprocess.run(
        ["git", "rev-parse", f"{head}^"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_is_ancestor(base: str, head: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=ROOT,
        check=False,
    ).returncode == 0


def _gh_json(endpoint: str, *fields: str) -> dict:
    command = ["gh", "api", "--method", "GET", endpoint]
    for field in fields:
        command.extend(["-f", field])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def successful_runs(repository: str) -> list[dict]:
    payload = _gh_json(
        f"repos/{repository}/actions/workflows/scpf.yml/runs",
        "branch=main",
        "status=success",
        "per_page=50",
    )
    return list(payload.get("workflow_runs") or [])


def has_qualification_artifact(repository: str, run_id: int, sha: str) -> bool:
    payload = _gh_json(
        f"repos/{repository}/actions/runs/{run_id}/artifacts",
        "per_page=100",
    )
    expected = f"scpf-qualification-{sha}"
    return any(
        item.get("name") == expected and not item.get("expired", False)
        for item in (payload.get("artifacts") or [])
    )


def select_reusable_run(repository: str, head: str) -> tuple[int, str]:
    for run in successful_runs(repository):
        candidate = str(run.get("head_sha") or "")
        run_id = int(run.get("id") or 0)
        if not candidate or not run_id:
            continue
        if not _git_is_ancestor(candidate, head):
            continue

        paths = changed_paths(candidate, head)
        if not reusable_paths(paths):
            continue
        if not has_qualification_artifact(repository, run_id, candidate):
            continue
        return run_id, candidate

    raise RuntimeError("no reusable successful qualification run found")


def _write_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    scope = sub.add_parser("scope")
    scope.add_argument("--base", default="")
    scope.add_argument("--head", required=True)
    scope.add_argument("--github-output", type=Path, required=True)

    select = sub.add_parser("select")
    select.add_argument("--head", required=True)
    select.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    select.add_argument("--github-output", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "scope":
        base = normalize_base(args.base, args.head)
        paths = changed_paths(base, args.head)
        allowed = reusable_paths(paths)
        print("Site publication scope: " + ("reusable" if allowed else "requires qualification"))
        for path in paths:
            print(f"  - {path}")
        _write_outputs(
            args.github_output,
            {"site_only": "true" if allowed else "false"},
        )
        return 0

    if not args.repository:
        raise SystemExit("--repository or GITHUB_REPOSITORY is required")
    run_id, sha = select_reusable_run(args.repository, args.head)
    print(f"Reusing qualification {sha} from run {run_id}")
    _write_outputs(
        args.github_output,
        {"run_id": str(run_id), "sha": sha},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
