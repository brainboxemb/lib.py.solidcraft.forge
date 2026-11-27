"""Publish complete or incremental successful model-owner output."""
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
    pass


def _run(command, *, cwd, check=True):
    return subprocess.run(
        command, cwd=cwd, check=check, capture_output=True, text=True
    )


def _remote_sha(repo, ref):
    result = _run(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{ref}"],
        cwd=repo,
    )
    line = result.stdout.strip()
    return line.split()[0] if line else None


def _require_fresh_source(repo, source_ref, source_sha):
    actual = _remote_sha(repo, source_ref)
    if actual != source_sha:
        raise PublishError(
            f"source ref moved: {source_ref} expected {source_sha}, found {actual}"
        )


def _prepare_worktree(repo, branch, target):
    fetch = _run(
        [
            "git", "fetch", "--no-tags", "origin",
            f"refs/heads/{branch}:refs/remotes/origin/{branch}",
        ],
        cwd=repo,
        check=False,
    )
    if fetch.returncode == 0:
        _run(
            [
                "git", "worktree", "add", "--detach", str(target),
                f"refs/remotes/origin/{branch}",
            ],
            cwd=repo,
        )
    else:
        _run(["git", "worktree", "add", "--detach", str(target), "HEAD"], cwd=repo)
        _run(["git", "switch", "--orphan", branch], cwd=target)
        _run(["git", "rm", "-rf", "."], cwd=target, check=False)
        for child in target.iterdir():
            if child.name != ".git":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    _run(["git", "config", "user.name", "github-actions[bot]"], cwd=target)
    _run(
        [
            "git", "config", "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ],
        cwd=target,
    )


def _preserve_release_baseline(plan, source_ref, stable_ref):
    """Return whether release-only stable metadata must not replace build/main."""

    if plan.get("release_only") is not True:
        return False
    if source_ref != stable_ref:
        raise PublishError("release-only publication is valid only for stable source")
    if plan.get("full") is True:
        raise PublishError("release-only candidate cannot be a full build")
    if plan.get("library") is not True:
        raise PublishError("release-only candidate must qualify the library")
    if plan.get("selected") not in ([], ()):
        raise PublishError("release-only candidate must not select model owners")
    probes = plan.get("api_probes", {})
    if isinstance(probes, dict) and probes.get("selected") not in (None, [], ()):
        raise PublishError("release-only candidate must not select API probes")
    return True


def update_scope(target, candidate, plan):
    active, selected = set(plan["active"]), set(plan["selected"])
    if not selected <= active or not all(
        re.fullmatch(r"[a-z0-9][a-z0-9_-]*", item) for item in active
    ):
        raise PublishError("invalid model selection")
    if plan["full"] and selected != active:
        raise PublishError("full build did not select all models")

    target.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(target / "examples", ignore_errors=True)
    existing = target / "models"
    existing.mkdir(exist_ok=True)

    for item in existing.iterdir():
        if item.name not in active or plan["full"]:
            shutil.rmtree(item) if item.is_dir() else item.unlink()

    for item in sorted(selected):
        source = candidate / "models" / item
        result = json.loads((source / "result.json").read_text())
        if result.get("status") != "pass" or result.get("id") != item:
            raise PublishError(f"cannot publish unsuccessful model: {item}")
        dest = existing / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        (dest / "source.json").write_text(
            json.dumps({"source_sha": plan["source_sha"]}, indent=2) + "\n"
        )

    missing = active - {p.name for p in existing.iterdir() if p.is_dir()}
    if missing:
        raise PublishError(f"missing successful model output: {sorted(missing)}")

    probe_plan = plan.get("api_probes", {"available": [], "selected": []})
    if not isinstance(probe_plan, dict):
        raise PublishError("invalid API probe selection")
    available_probes = set(probe_plan.get("available", []))
    selected_probes = set(probe_plan.get("selected", []))
    if (
        not selected_probes <= available_probes
        or not all(
            isinstance(item, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", item)
            for item in available_probes
        )
    ):
        raise PublishError("invalid API probe selection")

    probe_target = target / "api-probes"
    if selected_probes:
        probe_target.mkdir(parents=True, exist_ok=True)
    for item in sorted(selected_probes):
        source = candidate / "api-probes" / item
        result = json.loads((source / "result.json").read_text())
        if result.get("status") != "pass" or result.get("id") != item:
            raise PublishError(f"cannot publish unsuccessful API probe: {item}")
        dest = probe_target / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        (dest / "source.json").write_text(
            json.dumps({"source_sha": plan["source_sha"]}, indent=2) + "\n"
        )

    (target / "build-plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n"
    )


def publish(repo, candidate, source_ref, source_sha):
    repo, candidate = repo.resolve(), candidate.resolve()
    config = yaml.safe_load((repo / "ci.yml").read_text())
    if source_ref not in (
        config["branches"]["stable"],
        config["branches"]["development"],
        "exp",
    ):
        raise PublishError("publication requires permanent source branch")
    branch = config["generated"]["build_branch"]
    plan = json.loads((candidate / "build-plan.json").read_text())
    if plan.get("schema") != 2 or plan.get("source_sha") != source_sha:
        raise PublishError("candidate provenance mismatch")

    if _preserve_release_baseline(
        plan,
        source_ref,
        config["branches"]["stable"],
    ):
        _require_fresh_source(repo, source_ref, source_sha)
        return

    for _ in range(3):
        _require_fresh_source(repo, source_ref, source_sha)
        with tempfile.TemporaryDirectory(prefix="cad-build-publish-") as tmp:
            worktree = Path(tmp) / "worktree"
            try:
                _prepare_worktree(repo, branch, worktree)
                update_scope(worktree / source_ref, candidate, plan)
                _run(["git", "add", "-A", "--", source_ref], cwd=worktree)
                diff = _run(
                    ["git", "diff", "--cached", "--quiet"],
                    cwd=worktree,
                    check=False,
                )
                if diff.returncode == 0:
                    return
                _run(
                    ["git", "commit", "-m", f"build: {source_ref} {source_sha}"],
                    cwd=worktree,
                )
                _require_fresh_source(repo, source_ref, source_sha)
                push = _run(
                    ["git", "push", "origin", f"HEAD:refs/heads/{branch}"],
                    cwd=worktree,
                    check=False,
                )
                if push.returncode == 0:
                    return
            finally:
                _run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=repo,
                    check=False,
                )
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
