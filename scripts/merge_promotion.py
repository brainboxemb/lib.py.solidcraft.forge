#!/usr/bin/env python3
"""Prepare a merged PR's verified sparse overlay for build/main promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.impact import affected_cases, changed_paths, final_gate
from scripts.generated_output import load_manifest, promote_overlay


REQUIRED_LEVEL = {
    "regenerate-derived": "derived",
    "affected-q1-q2": "affected-q1-q2",
    "affected-q1-q6": "affected-q1-q6",
    "full-q1-q6": "q1-q6-full",
}


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def tree_sha(commit: str) -> str:
    return git_output("rev-parse", f"{commit}^{{tree}}")


def prepare(
    *,
    base_sha: str,
    head_sha: str,
    merge_sha: str,
    current_main_sha: str,
    pull_request: int,
    build_root: Path,
    destination: Path,
    workflow_run_id: str,
) -> dict:
    paths = changed_paths(base_sha, head_sha)
    cases = affected_cases(paths)
    gate = final_gate(paths, cases)
    result = {
        "technical": gate != "preflight",
        "current_main": current_main_sha,
        "merge_is_current_main": merge_sha == current_main_sha,
        "release_candidate": "scpf/pyproject.toml" in paths,
        "cases": ",".join(cases),
        "final_gate": gate,
        "tree_match": tree_sha(head_sha) == tree_sha(merge_sha),
        "promotable": False,
    }
    if not result["technical"]:
        return result
    if not result["merge_is_current_main"]:
        return result

    overlay = build_root / "pr" / str(pull_request)
    manifest = load_manifest(overlay)
    if manifest.get("source_commit") != head_sha:
        raise RuntimeError(
            "PR overlay head does not match merged PR head"
        )
    if manifest.get("base_commit") != base_sha:
        raise RuntimeError(
            "PR overlay base does not match merged PR base"
        )
    if not result["tree_match"]:
        return result

    required = REQUIRED_LEVEL.get(gate)
    if not required:
        raise RuntimeError(
            f"technical merge has unsupported final gate {gate}"
        )
    promote_overlay(
        build_root / "main",
        overlay,
        destination,
        required_level=required,
        source_commit=merge_sha,
        workflow_run_id=workflow_run_id,
    )
    result["promotable"] = True
    result["required_level"] = required
    return result


def write_outputs(path: Path, data: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in data.items():
            if isinstance(value, bool):
                value = "true" if value else "false"
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--merge-sha", required=True)
    parser.add_argument("--current-main-sha", required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    result = prepare(
        base_sha=args.base_sha,
        head_sha=args.head_sha,
        merge_sha=args.merge_sha,
        current_main_sha=args.current_main_sha,
        pull_request=args.pull_request,
        build_root=args.build_root,
        destination=args.destination,
        workflow_run_id=args.workflow_run_id,
    )
    print(json.dumps(result, indent=2))
    if args.github_output:
        write_outputs(args.github_output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
