"""Find a safe incremental baseline and changed Git paths."""

from __future__ import annotations

import json
from dataclasses import dataclass
import subprocess
from urllib import parse, request


class HistoryError(RuntimeError):
    """GitHub or Git history cannot provide a safe incremental baseline."""


@dataclass(frozen=True)
class ReusableQualification:
    pr_number: int
    head_sha: str
    base_sha: str
    run_id: int
    artifact_id: int


def _json(url: str, token: str):
    req = request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with request.urlopen(req) as response:
        return json.load(response)


def last_successful_dev_sha(
    *,
    repository: str,
    branch: str,
    token: str,
    current_run_id: int,
    target_sha: str,
    workflow_file: str = "ci.yml",
) -> str | None:
    branch_value = parse.quote(branch, safe="")
    workflow_value = parse.quote(workflow_file, safe="")
    url = (
        f"https://api.github.com/repos/{repository}/actions/workflows/"
        f"{workflow_value}/runs?branch={branch_value}&status=success&per_page=100"
    )
    runs = _json(url, token).get("workflow_runs", [])
    for run in runs:
        if run.get("id") == current_run_id:
            continue
        if run.get("event") not in {"push", "workflow_dispatch"}:
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            continue
        sha = run.get("head_sha")
        if isinstance(sha, str) and sha and sha != target_sha:
            return sha
    return None


def changed_paths(repo, baseline: str, target: str) -> tuple[str, ...] | None:
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", baseline, target],
        check=False,
    )
    if ancestor.returncode != 0:
        return None

    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", baseline, target, "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    )


def changed_paths_from_parent(repo, target: str) -> tuple[str, ...] | None:
    """Return one single-parent commit delta, or None for merge/root commits."""

    result = subprocess.run(
        ["git", "-C", str(repo), "rev-list", "--parents", "-n", "1", target],
        check=True,
        capture_output=True,
        text=True,
    )
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None
    return changed_paths(repo, parts[1], target)


def changed_paths_from_base(repo, base_ref: str, target: str = "HEAD") -> tuple[str, ...] | None:
    """Return the PR delta from the remote base branch to target."""

    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", target, f"origin/{base_ref}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    baseline = result.stdout.strip()
    if not baseline:
        return None
    return changed_paths(repo, baseline, target)


def reusable_pr_qualification(
    *,
    repository: str,
    branch: str,
    token: str,
    source_sha: str,
    pr_number: int,
    head_sha: str,
    run_id: int,
    artifact_name: str = "cad-qualification",
) -> ReusableQualification | None:
    """Validate merge-policy-bound PR evidence for one permanent commit."""

    repo_value = parse.quote(repository, safe="/")
    pr = _json(
        f"https://api.github.com/repos/{repo_value}/pulls/{pr_number}",
        token,
    )
    if not isinstance(pr, dict):
        return None
    head = pr.get("head") or {}
    base = pr.get("base") or {}
    head_repo = head.get("repo") or {}
    base_sha = base.get("sha")
    if (
        pr.get("state") != "closed"
        or not pr.get("merged_at")
        or pr.get("merge_commit_sha") != source_sha
        or base.get("ref") != branch
        or head_repo.get("full_name") != repository
        or head.get("sha") != head_sha
        or not isinstance(base_sha, str)
        or not base_sha
    ):
        return None

    run = _json(
        f"https://api.github.com/repos/{repo_value}/actions/runs/{run_id}",
        token,
    )
    if (
        not isinstance(run, dict)
        or run.get("id") != run_id
        or run.get("event") != "pull_request"
        or run.get("path") != ".github/workflows/ci.yml"
        or run.get("head_sha") != head_sha
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
    ):
        return None
    head_branch = run.get("head_branch")
    if isinstance(head_branch, str) and head_branch and head_branch != head.get("ref"):
        return None

    artifacts = _json(
        f"https://api.github.com/repos/{repo_value}/actions/runs/{run_id}/artifacts"
        "?per_page=100",
        token,
    ).get("artifacts", [])
    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("name") == artifact_name
        and artifact.get("expired") is False
        and type(artifact.get("id")) is int
    ]
    if len(matches) != 1:
        return None

    return ReusableQualification(
        pr_number=pr_number,
        head_sha=head_sha,
        base_sha=base_sha,
        run_id=run_id,
        artifact_id=matches[0]["id"],
    )



def discover_reusable_pr_qualification(
    *,
    repository: str,
    branch: str,
    token: str,
    source_sha: str,
    artifact_name: str = "cad-qualification",
) -> ReusableQualification | None:
    """Conservatively discover reusable PR evidence when merge policy gave no binding.

    GitHub may remove pull-request associations from completed Actions runs after
    merge. The permanent commit still retains its associated merged PR. Use that
    PR to obtain the exact reviewed base/head, then consider only the newest
    central pull-request CI run for the same head/ref. The artifact's synthetic
    PR merge commit is validated separately by reuse.py before evidence can be
    accepted.
    """

    repo_value = parse.quote(repository, safe="/")
    source_value = parse.quote(source_sha, safe="")
    pulls = _json(
        f"https://api.github.com/repos/{repo_value}/commits/{source_value}/pulls",
        token,
    )
    if not isinstance(pulls, list):
        return None

    candidates = []
    for pr in pulls:
        if not isinstance(pr, dict):
            continue
        head = pr.get("head") or {}
        base = pr.get("base") or {}
        head_repo = head.get("repo") or {}
        if (
            pr.get("state") == "closed"
            and pr.get("merged_at")
            and pr.get("merge_commit_sha") == source_sha
            and base.get("ref") == branch
            and head_repo.get("full_name") == repository
            and isinstance(head.get("sha"), str)
            and head.get("sha")
            and isinstance(head.get("ref"), str)
            and head.get("ref")
            and isinstance(base.get("sha"), str)
            and base.get("sha")
            and type(pr.get("number")) is int
        ):
            candidates.append(pr)
    if len(candidates) != 1:
        return None

    pr = candidates[0]
    head = pr["head"]
    base = pr["base"]
    head_sha = head["sha"]
    head_ref = head["ref"]
    head_value = parse.quote(head_sha, safe="")
    runs = _json(
        f"https://api.github.com/repos/{repo_value}/actions/runs"
        f"?head_sha={head_value}&event=pull_request&per_page=100",
        token,
    ).get("workflow_runs", [])
    ci_runs = [
        run
        for run in runs
        if isinstance(run, dict)
        and run.get("event") == "pull_request"
        and run.get("path") == ".github/workflows/ci.yml"
        and run.get("head_sha") == head_sha
        and run.get("head_branch") in (None, "", head_ref)
        and type(run.get("id")) is int
    ]
    if not ci_runs:
        return None

    def recency(run):
        created = run.get("created_at")
        if not isinstance(created, str):
            created = ""
        return created, run["id"]

    latest = max(ci_runs, key=recency)
    if (
        latest.get("status") != "completed"
        or latest.get("conclusion") != "success"
    ):
        return None

    run_id = latest["id"]
    artifacts = _json(
        f"https://api.github.com/repos/{repo_value}/actions/runs/{run_id}/artifacts"
        "?per_page=100",
        token,
    ).get("artifacts", [])
    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("name") == artifact_name
        and artifact.get("expired") is False
        and type(artifact.get("id")) is int
    ]
    if len(matches) != 1:
        return None

    return ReusableQualification(
        pr_number=pr["number"],
        head_sha=head_sha,
        base_sha=base["sha"],
        run_id=run_id,
        artifact_id=matches[0]["id"],
    )
