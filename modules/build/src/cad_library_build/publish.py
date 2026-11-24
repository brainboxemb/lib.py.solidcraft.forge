"""Publish complete or incremental successful example output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import yaml

class PublishError(RuntimeError):
    """Build publication failed."""


def _run(command: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _remote_sha(repo: Path, ref: str) -> str | None:
    result = _run(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{ref}"],
        cwd=repo,
    )
    line = result.stdout.strip()
    if not line:
        return None
    return line.split()[0]


def _require_fresh_source(repo: Path, source_ref: str, source_sha: str) -> None:
    actual = _remote_sha(repo, source_ref)
    if actual != source_sha:
        raise PublishError(
            f"source ref moved: {source_ref} expected {source_sha}, found {actual}"
        )


def _prepare_worktree(repo: Path, branch: str, target: Path) -> bool:
    fetch = _run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            f"refs/heads/{branch}:refs/remotes/origin/{branch}",
        ],
        cwd=repo,
        check=False,
    )
    exists = fetch.returncode == 0
    if exists:
        _run(
            ["git", "worktree", "add", "--detach", str(target), f"refs/remotes/origin/{branch}"],
            cwd=repo,
        )
    else:
        _run(["git", "worktree", "add", "--detach", str(target), "HEAD"], cwd=repo)
        _run(["git", "switch", "--orphan", branch], cwd=target)
        _run(["git", "rm", "-rf", "."], cwd=target, check=False)
        for child in target.iterdir():
            if child.name != ".git":
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    _run(["git", "config", "user.name", "github-actions[bot]"], cwd=target)
    _run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ],
        cwd=target,
    )
    return exists



def update_scope(target: Path, candidate: Path, plan: dict):
    active, selected = set(plan["active"]), set(plan["selected"])
    if not selected <= active or not all(re.fullmatch(r"[a-z0-9][a-z0-9_-]*", item) for item in active):
        raise PublishError("invalid example selection")
    if plan["full"] and selected != active:
        raise PublishError("full build did not select all examples")
    target.mkdir(parents=True, exist_ok=True)
    existing = target / "examples"
    existing.mkdir(exist_ok=True)
    for item in existing.iterdir():
        if item.name not in active or plan["full"]:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    for item in sorted(selected):
        source = candidate / "examples" / item
        result = json.loads((source / "result.json").read_text())
        if result.get("status") != "pass" or result.get("id") != item:
            raise PublishError(f"cannot publish unsuccessful example: {item}")
        dest = existing / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        (dest / "source.json").write_text(json.dumps({"source_sha": plan["source_sha"]}, indent=2) + "\n")
    missing = active - {p.name for p in existing.iterdir() if p.is_dir()}
    if missing:
        raise PublishError(f"missing successful build output: {sorted(missing)}")
    (target / "build-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")


def publish(repo: Path, candidate: Path, source_ref: str, source_sha: str):
    repo, candidate = repo.resolve(), candidate.resolve()
    config = yaml.safe_load((repo / "ci.yml").read_text())
    if source_ref not in (config["branches"]["stable"], config["branches"]["development"]):
        raise PublishError("publication requires permanent source branch")
    branch = config["generated"]["build_branch"]
    plan = json.loads((candidate / "build-plan.json").read_text())
    if plan.get("schema") != 1 or plan.get("source_sha") != source_sha:
        raise PublishError("candidate provenance mismatch")
    for _ in range(3):
        _require_fresh_source(repo, source_ref, source_sha)
        with tempfile.TemporaryDirectory(prefix="cad-build-publish-") as tmp:
            worktree = Path(tmp) / "worktree"
            try:
                _prepare_worktree(repo, branch, worktree)
                update_scope(worktree / source_ref, candidate, plan)
                _run(["git", "add", "-A", "--", source_ref], cwd=worktree)
                diff = _run(["git", "diff", "--cached", "--quiet"], cwd=worktree, check=False)
                if diff.returncode == 0:
                    return
                _run(["git", "commit", "-m", f"build: {source_ref} {source_sha}"], cwd=worktree)
                _require_fresh_source(repo, source_ref, source_sha)
                if _run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=worktree, check=False).returncode == 0:
                    return
            finally:
                _run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo, check=False)
                _run(["git", "worktree", "prune"], cwd=repo, check=False)
    raise PublishError("build publication failed after three attempts")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    publish(args.repo, args.candidate, args.source_ref, args.source_sha)


if __name__ == "__main__":
    main()
