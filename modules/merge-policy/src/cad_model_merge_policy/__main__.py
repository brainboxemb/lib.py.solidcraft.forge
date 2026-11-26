"""Execute repository-local merge policy."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from urllib import error, request

from .policy import (
    MergePolicyError,
    is_main_governance,
    is_permanent_merge,
    merge_method,
)
from .resolution import parse_resolution_command, verify_merge_object


_ALLOWED_CI_RESULTS = {"success", "neutral", "skipped"}
_MAIN_GOVERNANCE_PATHS = frozenset({
    "AGENTS.md",
    "docs/plan.md",
    "docs/handoff.md",
})


def api(repository: str, path: str, token: str, *, method: str = "GET", body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = request.Request(
        f"https://api.github.com/repos/{repository}/{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with request.urlopen(req) as response:
            if response.status == 204:
                return None
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MergePolicyError(f"GitHub API {exc.code}: {detail}") from exc


def pull_request_files(
    repository: str,
    pull_request_number: int,
    token: str,
) -> tuple[str, ...]:
    """Return every changed path, following GitHub's PR-files pagination."""

    result = []
    page = 1
    while True:
        rows = api(
            repository,
            f"pulls/{pull_request_number}/files?per_page=100&page={page}",
            token,
        )
        if not isinstance(rows, list):
            raise MergePolicyError("pull request files response must be a list")
        for row in rows:
            filename = row.get("filename") if isinstance(row, dict) else None
            if not isinstance(filename, str) or not filename:
                raise MergePolicyError("pull request file has no filename")
            result.append(filename)
        if len(rows) < 100:
            break
        page += 1
    return tuple(result)


def require_main_governance_paths(
    repository: str,
    pull_request_number: int,
    token: str,
) -> None:
    """Fail closed unless a docs->main PR is governance-only."""

    paths = pull_request_files(repository, pull_request_number, token)
    if not paths:
        raise MergePolicyError("main governance pull request has no changed files")
    forbidden = sorted(set(paths) - _MAIN_GOVERNANCE_PATHS)
    if forbidden:
        raise MergePolicyError(
            "main governance pull request may change only "
            "AGENTS.md, docs/plan.md and docs/handoff.md; "
            f"forbidden: {', '.join(forbidden)}"
        )


def _workflow_run_recency(run: dict) -> tuple[str, int]:
    """Return one deterministic GitHub Actions run recency key."""

    created = run.get("created_at")
    if not isinstance(created, str):
        created = ""
    run_id = run.get("id")
    if not isinstance(run_id, int) or isinstance(run_id, bool):
        run_id = -1
    return created, run_id


def require_green_ci(
    repository: str,
    sha: str,
    pull_request_number: int,
    token: str,
) -> None:
    """Require the latest central pull-request CI for this exact head SHA.

    GitHub can re-associate historical check-runs with a replacement PR when
    the same head commit is reused. Query pull-request workflow runs directly
    and validate only the newest run for this PR so superseded failures do not
    poison a later successful qualification.
    """

    payload = api(
        repository,
        (
            "actions/runs"
            f"?head_sha={sha}&event=pull_request&per_page=100"
        ),
        token,
    )
    runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
    ci_runs = [
        run
        for run in runs
        if isinstance(run, dict)
        and run.get("event") == "pull_request"
        and run.get("path") == ".github/workflows/ci.yml"
        and any(
            pr.get("number") == pull_request_number
            for pr in run.get("pull_requests", [])
            if isinstance(pr, dict)
        )
    ]

    if not ci_runs:
        raise MergePolicyError("pull request has no central ci check")

    latest = max(ci_runs, key=_workflow_run_recency)
    if latest.get("status") != "completed":
        raise MergePolicyError("central ci check is still running")
    if latest.get("conclusion") not in _ALLOWED_CI_RESULTS:
        raise MergePolicyError("central ci check is not green")


def require_durable_permanent_head(
    repository: str,
    branch: str,
    sha: str,
    token: str,
) -> None:
    """Require published permanent qualification for the exact branch source.

    A genuinely conflicted pull request has no synthetic merge ref, so GitHub
    may not start its pull-request workflow at all. Permanent qualification
    already records the actual checked-out source SHA in durable build evidence;
    use that source identity for the original conflicted head while the separate
    resolution review still requires normal pull-request CI.
    """

    payload = api(
        repository,
        f"contents/{branch}/build-plan.json?ref=build",
        token,
    )
    if not isinstance(payload, dict):
        raise MergePolicyError("permanent head has no durable build evidence")
    content = payload.get("content")
    if payload.get("encoding") != "base64" or not isinstance(content, str):
        raise MergePolicyError("permanent head build evidence is malformed")

    try:
        raw = base64.b64decode(
            "".join(content.splitlines()),
            validate=True,
        ).decode("utf-8")
        plan = json.loads(raw)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MergePolicyError(
            "permanent head build evidence is malformed"
        ) from exc

    source_sha = plan.get("source_sha") if isinstance(plan, dict) else None
    if source_sha != sha:
        raise MergePolicyError(
            "permanent head durable qualification does not match reviewed SHA"
        )


def merge_required(pr: dict) -> bool:
    if pr.get("merged"):
        return False
    if pr.get("state") != "open":
        raise MergePolicyError("pull request is closed without merge")
    return True


def dispatch_workflow(repository: str, workflow: str, ref: str, token: str) -> None:
    api(
        repository,
        f"actions/workflows/{workflow}/dispatches",
        token,
        method="POST",
        body={"ref": ref},
    )


def branch_sha(repository: str, branch: str, token: str) -> str:
    payload = api(repository, f"git/ref/heads/{branch}", token)
    sha = (payload.get("object") or {}).get("sha") if isinstance(payload, dict) else None
    if not isinstance(sha, str) or len(sha) != 40:
        raise MergePolicyError(f"branch {branch!r} has no exact commit SHA")
    return sha


def require_branch_sha(
    repository: str,
    branch: str,
    expected: str,
    token: str,
    *,
    label: str,
) -> None:
    actual = branch_sha(repository, branch, token)
    if actual != expected:
        raise MergePolicyError(
            f"{label} moved: {branch} expected {expected}, current {actual}"
        )


def require_conflicted_permanent_pr(
    repository: str,
    pull_request_number: int,
    expected_base_sha: str,
    expected_head_sha: str,
    token: str,
) -> dict:
    """Require the original direct permanent PR at its reviewed parents."""

    pr = api(repository, f"pulls/{pull_request_number}", token)
    if not isinstance(pr, dict) or not merge_required(pr):
        raise MergePolicyError("resolved merge requires an open pull request")
    if pr.get("draft") is not False:
        raise MergePolicyError("resolved merge requires a non-draft pull request")
    base = pr.get("base") or {}
    head = pr.get("head") or {}
    if base.get("sha") != expected_base_sha:
        raise MergePolicyError("reviewed base SHA no longer matches pull request")
    if head.get("sha") != expected_head_sha:
        raise MergePolicyError("reviewed head SHA no longer matches pull request")
    if pr.get("mergeable") is not False:
        if pr.get("mergeable") is True:
            raise MergePolicyError("pull request is mergeable; use normal /merge")
        raise MergePolicyError("pull request mergeability is not resolved yet")

    base_ref = base.get("ref")
    head_ref = head.get("ref")
    head_repo = (head.get("repo") or {}).get("full_name")
    if head_repo != repository:
        raise MergePolicyError("permanent merge must originate in this repository")
    if not is_permanent_merge(head=head_ref, base=base_ref):
        raise MergePolicyError(
            f"/merge-resolved is only valid for a direct permanent merge: "
            f"{head_ref} -> {base_ref}"
        )
    return pr


def require_resolution_review(
    repository: str,
    original_number: int,
    original_pr: dict,
    resolution_pr: int,
    resolution_ref: str,
    resolution_sha: str,
    base_sha: str,
    token: str,
) -> dict:
    """Require one separate mergeable green PR exposing the reviewed tree."""

    if resolution_pr == original_number:
        raise MergePolicyError("resolution review PR must be separate")

    review = api(repository, f"pulls/{resolution_pr}", token)
    if not isinstance(review, dict) or review.get("state") != "open":
        raise MergePolicyError("resolution review PR must be open")
    if review.get("draft") is not False:
        raise MergePolicyError("resolution review PR must not be draft")
    if review.get("mergeable") is not True:
        raise MergePolicyError("resolution review PR must be mergeable")

    base = review.get("base") or {}
    head = review.get("head") or {}
    original_base = original_pr.get("base") or {}
    if base.get("ref") != original_base.get("ref") or base.get("sha") != base_sha:
        raise MergePolicyError(
            "resolution review PR must target the exact conflicted base"
        )
    if (head.get("repo") or {}).get("full_name") != repository:
        raise MergePolicyError("resolution review PR must originate in this repository")
    if head.get("ref") != resolution_ref or head.get("sha") != resolution_sha:
        raise MergePolicyError(
            "resolution review PR does not match reviewed resolution ref/commit"
        )

    require_green_ci(repository, resolution_sha, resolution_pr, token)
    return review


def resolution_commit_tree(
    repository: str,
    resolution_sha: str,
    expected_tree: str,
    token: str,
) -> None:
    payload = api(repository, f"git/commits/{resolution_sha}", token)
    actual = (payload.get("tree") or {}).get("sha") if isinstance(payload, dict) else None
    if actual != expected_tree:
        raise MergePolicyError(
            "resolution commit tree mismatch: "
            f"expected {expected_tree}, current {actual}"
        )


def close_pr_if_open(
    repository: str,
    pull_request_number: int,
    token: str,
) -> None:
    pr = api(repository, f"pulls/{pull_request_number}", token)
    if isinstance(pr, dict) and pr.get("state") == "open":
        api(
            repository,
            f"pulls/{pull_request_number}",
            token,
            method="PATCH",
            body={"state": "closed"},
        )


def delete_resolution_ref(
    repository: str,
    resolution_ref: str,
    resolution_sha: str,
    token: str,
) -> None:
    require_branch_sha(
        repository,
        resolution_ref,
        resolution_sha,
        token,
        label="resolution ref",
    )
    api(
        repository,
        f"git/refs/heads/{resolution_ref}",
        token,
        method="DELETE",
    )


def run_resolved(args, token: str) -> str:
    """Apply one reviewed tree to a genuinely conflicted permanent merge."""

    resolved = parse_resolution_command(args.command, args.resolution_prefix)
    pr = require_conflicted_permanent_pr(
        args.repository,
        args.pull_request_number,
        resolved.base_sha,
        resolved.head_sha,
        token,
    )
    base = pr["base"]["ref"]
    head = pr["head"]["ref"]

    require_branch_sha(
        args.repository,
        head,
        resolved.head_sha,
        token,
        label="head ref",
    )
    require_durable_permanent_head(
        args.repository,
        head,
        resolved.head_sha,
        token,
    )
    review = require_resolution_review(
        args.repository,
        args.pull_request_number,
        pr,
        resolved.resolution_pr,
        resolved.resolution_ref,
        resolved.resolution_sha,
        resolved.base_sha,
        token,
    )

    require_branch_sha(
        args.repository,
        base,
        resolved.base_sha,
        token,
        label="base ref",
    )
    require_branch_sha(
        args.repository,
        head,
        resolved.head_sha,
        token,
        label="head ref",
    )
    require_branch_sha(
        args.repository,
        resolved.resolution_ref,
        resolved.resolution_sha,
        token,
        label="resolution ref",
    )
    resolution_commit_tree(
        args.repository,
        resolved.resolution_sha,
        resolved.resolution_tree,
        token,
    )

    # Re-read both PRs immediately before creating the merge object.
    current = require_conflicted_permanent_pr(
        args.repository,
        args.pull_request_number,
        resolved.base_sha,
        resolved.head_sha,
        token,
    )
    require_resolution_review(
        args.repository,
        args.pull_request_number,
        current,
        resolved.resolution_pr,
        resolved.resolution_ref,
        resolved.resolution_sha,
        resolved.base_sha,
        token,
    )

    created = api(
        args.repository,
        "git/commits",
        token,
        method="POST",
        body={
            "message": (
                f"Merge {head} into {base} "
                f"(reviewed conflict resolution PR #{resolved.resolution_pr})"
            ),
            "tree": resolved.resolution_tree,
            "parents": [resolved.base_sha, resolved.head_sha],
        },
    )
    merge_sha = verify_merge_object(
        created,
        expected_tree=resolved.resolution_tree,
        expected_parents=(resolved.base_sha, resolved.head_sha),
    )

    # Nothing mutable may move between merge-object creation and base advance.
    require_branch_sha(
        args.repository,
        base,
        resolved.base_sha,
        token,
        label="base ref",
    )
    require_branch_sha(
        args.repository,
        head,
        resolved.head_sha,
        token,
        label="head ref",
    )
    require_branch_sha(
        args.repository,
        resolved.resolution_ref,
        resolved.resolution_sha,
        token,
        label="resolution ref",
    )
    resolution_commit_tree(
        args.repository,
        resolved.resolution_sha,
        resolved.resolution_tree,
        token,
    )

    api(
        args.repository,
        f"git/refs/heads/{base}",
        token,
        method="PATCH",
        body={"sha": merge_sha, "force": False},
    )

    dispatch_workflow(args.repository, "ci.yml", base, token)
    dispatch_workflow(args.repository, "branch-cleanup.yml", base, token)

    close_pr_if_open(args.repository, args.pull_request_number, token)
    close_pr_if_open(args.repository, resolved.resolution_pr, token)
    delete_resolution_ref(
        args.repository,
        resolved.resolution_ref,
        resolved.resolution_sha,
        token,
    )

    # Keep the read variable intentionally used: it documents that the exact
    # review PR passed the pre-mutation validation above.
    if review.get("number") not in (None, resolved.resolution_pr):
        raise MergePolicyError("resolution review identity changed unexpectedly")

    return merge_sha


def run_normal(args, token: str) -> str:
    pr = api(args.repository, f"pulls/{args.pull_request_number}", token)
    if not merge_required(pr):
        return pr.get("merge_commit_sha") or "already merged"
    if pr.get("draft") is not False:
        raise MergePolicyError("pull request is still a draft")

    base = pr["base"]["ref"]
    head = pr["head"]["ref"]
    method = merge_method(head=head, base=base)
    if is_main_governance(head=head, base=base):
        require_main_governance_paths(
            args.repository,
            args.pull_request_number,
            token,
        )
    head_sha = pr["head"]["sha"]
    require_green_ci(
        args.repository,
        head_sha,
        args.pull_request_number,
        token,
    )

    result = api(
        args.repository,
        f"pulls/{args.pull_request_number}/merge",
        token,
        method="PUT",
        body={"sha": head_sha, "merge_method": method},
    )
    if not result.get("merged"):
        raise MergePolicyError(result.get("message", "GitHub did not merge PR"))

    dispatch_workflow(args.repository, "ci.yml", base, token)
    dispatch_workflow(args.repository, "branch-cleanup.yml", base, token)
    return result["sha"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-request-number", required=True, type=int)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repository-owner", required=True)
    parser.add_argument("--resolution-prefix", default="resolve/")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        raise MergePolicyError("GH_TOKEN is required")
    if args.actor != args.repository_owner:
        raise MergePolicyError("only the repository owner may execute merge commands")

    if args.command == "/merge":
        print(run_normal(args, token))
        return
    if args.command.startswith("/merge-resolved"):
        print(run_resolved(args, token))
        return
    raise MergePolicyError("command must be /merge or reviewed /merge-resolved")


if __name__ == "__main__":
    main()
