#!/usr/bin/env python3
"""Audit and reconcile PR-generated namespaces against live GitHub PR state."""

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

from scripts.publish_generated import publish


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def open_prs(repository: str) -> dict[int, str]:
    result = run(
        [
            "gh",
            "api",
            "--method",
            "GET",
            f"repos/{repository}/pulls",
            "-f",
            "state=open",
            "-f",
            "per_page=100",
        ]
    )
    data = json.loads(result.stdout)
    return {
        int(item["number"]): str(item["head"]["sha"])
        for item in data
    }


def fetch_generated() -> None:
    run(["git", "fetch", "--no-tags", "origin", "build", "gh-pages"])


def tree_dirs(ref: str, path: str) -> set[str]:
    completed = run(
        ["git", "ls-tree", "-d", "--name-only", f"{ref}:{path}"],
        check=False,
    )
    if completed.returncode != 0:
        return set()
    return {
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    }


def json_at(ref: str, path: str) -> dict | None:
    completed = run(["git", "show", f"{ref}:{path}"], check=False)
    if completed.returncode != 0:
        return None
    return json.loads(completed.stdout)


def audit(repository: str) -> dict:
    fetch_generated()
    current = open_prs(repository)
    build_ids = {
        int(name)
        for name in tree_dirs("origin/build", "pr")
        if name.isdigit()
    }
    preview_ids = {
        int(name.removeprefix("pr-"))
        for name in tree_dirs("origin/gh-pages", "previews")
        if name.startswith("pr-")
        and name.removeprefix("pr-").isdigit()
    }

    orphan_build = sorted(build_ids - set(current))
    orphan_preview = sorted(preview_ids - set(current))
    stale_build = []
    stale_preview = []

    for number, head in current.items():
        manifest = json_at("origin/build", f"pr/{number}/build.json")
        if manifest and manifest.get("source_commit") != head:
            stale_build.append(number)
        provenance = json_at(
            "origin/gh-pages",
            f"previews/pr-{number}/provenance.json",
        )
        if provenance and provenance.get("source_commit") != head:
            stale_preview.append(number)

    return {
        "open_prs": current,
        "orphan_build": orphan_build,
        "orphan_preview": orphan_preview,
        "stale_build": sorted(stale_build),
        "stale_preview": sorted(stale_preview),
    }


def reconcile(repository: str, *, apply: bool) -> dict:
    result = audit(repository)
    if not apply:
        return result

    for number in sorted(
        set(result["orphan_build"]) | set(result["stale_build"])
    ):
        publish(
            branch="build",
            operation="remove-dir",
            destination=f"pr/{number}",
            message=f"Reconcile build PR #{number}",
        )
    for number in sorted(
        set(result["orphan_preview"]) | set(result["stale_preview"])
    ):
        publish(
            branch="gh-pages",
            operation="remove-dir",
            destination=f"previews/pr-{number}",
            message=f"Reconcile preview PR #{number}",
        )
    result["applied"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.repository:
        raise SystemExit("--repository or GITHUB_REPOSITORY is required")
    result = reconcile(args.repository, apply=args.apply)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
