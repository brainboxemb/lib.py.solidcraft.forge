"""Publish selected API probe evidence without touching model output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
import yaml

from .publish import (
    PublishError,
    _prepare_worktree,
    _require_fresh_source,
    _run,
)


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def update_probe_scope(target, candidate, plan):
    available = plan.get("available")
    selected = plan.get("selected")
    if (
        not isinstance(available, list)
        or not isinstance(selected, list)
        or not all(isinstance(item, str) and _ID.fullmatch(item) for item in available)
        or not all(isinstance(item, str) and _ID.fullmatch(item) for item in selected)
        or not set(selected) <= set(available)
    ):
        raise PublishError("invalid API probe selection")

    root = target / "api-probes"
    root.mkdir(parents=True, exist_ok=True)

    for item in selected:
        source = candidate / "api-probes" / item
        result_path = source / "result.json"
        if not result_path.is_file():
            raise PublishError(f"missing API probe result: {item}")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("status") != "pass" or result.get("id") != item:
            raise PublishError(f"cannot publish unsuccessful API probe: {item}")

        dest = root / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        (dest / "source.json").write_text(
            json.dumps({"source_sha": plan["source_sha"]}, indent=2) + "\n",
            encoding="utf-8",
        )


def publish(repo, candidate, source_ref, source_sha):
    repo, candidate = repo.resolve(), candidate.resolve()
    config = yaml.safe_load((repo / "ci.yml").read_text(encoding="utf-8"))
    allowed = {
        config["branches"]["stable"],
        config["branches"]["development"],
        "exp",
    }
    if source_ref not in allowed:
        raise PublishError("durable API probe publication requires a permanent source ref")

    plan = json.loads(
        (candidate / "api-probe-plan.json").read_text(encoding="utf-8")
    )
    if plan.get("schema") != 1 or plan.get("source_sha") != source_sha:
        raise PublishError("API probe candidate provenance mismatch")

    branch = config["generated"]["build_branch"]
    for _ in range(3):
        _require_fresh_source(repo, source_ref, source_sha)
        with tempfile.TemporaryDirectory(prefix="cad-probe-publish-") as tmp:
            worktree = Path(tmp) / "worktree"
            try:
                _prepare_worktree(repo, branch, worktree)
                scope = worktree / source_ref
                update_probe_scope(scope, candidate, plan)
                _run(
                    ["git", "add", "-A", "--", f"{source_ref}/api-probes"],
                    cwd=worktree,
                )
                diff = _run(
                    ["git", "diff", "--cached", "--quiet"],
                    cwd=worktree,
                    check=False,
                )
                if diff.returncode == 0:
                    return
                _run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"build: api-probes {source_ref} {source_sha}",
                    ],
                    cwd=worktree,
                )
                _require_fresh_source(repo, source_ref, source_sha)
                pushed = _run(
                    ["git", "push", "origin", f"HEAD:refs/heads/{branch}"],
                    cwd=worktree,
                    check=False,
                )
                if pushed.returncode == 0:
                    return
            finally:
                _run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=repo,
                    check=False,
                )
                _run(["git", "worktree", "prune"], cwd=repo, check=False)

    raise PublishError("API probe publication failed after three attempts")


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
