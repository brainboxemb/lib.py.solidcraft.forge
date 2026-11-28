"""Materialize reusable PR qualification for one permanent source commit."""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import shutil
from urllib import error, parse, request
import zipfile

from .config import ConfigError, load_project
from .history import (
    _json,
    discover_reusable_pr_qualification,
    reusable_pr_qualification,
)


def _write_output(path: Path, **values):
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


class _NoRedirect(request.HTTPRedirectHandler):
    """Expose GitHub's signed artifact redirect without forwarding credentials."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _download_artifact(repository: str, artifact_id: int, token: str) -> bytes:
    """Download one Actions artifact without leaking GitHub auth cross-host."""
    repo_value = parse.quote(repository, safe="/")
    req = request.Request(
        f"https://api.github.com/repos/{repo_value}/actions/artifacts/"
        f"{artifact_id}/zip",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "cad-library-ci",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    opener = request.build_opener(_NoRedirect())
    try:
        with opener.open(req) as response:
            if response.status == 200:
                return response.read()
            location = response.headers.get("Location")
    except error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers.get("Location")

    if not isinstance(location, str) or not location.startswith("https://"):
        raise ValueError("artifact download did not return a signed redirect")

    # The signed object-storage URL already carries its own credentials.
    # Never forward the GitHub bearer token to that different host.
    blob_req = request.Request(
        location,
        headers={"User-Agent": "cad-library-ci"},
    )
    with request.urlopen(blob_req) as response:
        return response.read()


def _extract_zip(data: bytes, candidate: Path):
    candidate.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("qualification artifact contains unsafe path")
        archive.extractall(candidate)


def _commit(repository: str, sha: str, token: str) -> dict:
    repo_value = parse.quote(repository, safe="/")
    sha_value = parse.quote(sha, safe="")
    commit = _json(
        f"https://api.github.com/repos/{repo_value}/git/commits/{sha_value}",
        token,
    )
    if not isinstance(commit, dict):
        raise ValueError("cannot resolve qualification commit")
    return commit


def _artifact_source(candidate: Path) -> str:
    path = candidate / "build-plan.json"
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "qualification artifact has no valid build-plan.json"
        ) from exc
    source = plan.get("source_sha")
    if plan.get("schema") != 2 or not isinstance(source, str) or not source:
        raise ValueError("qualification artifact provenance mismatch")
    return source


def _require_same_qualified_tree(
    *,
    repository: str,
    source_sha: str,
    qualified_source_sha: str,
    base_sha: str,
    head_sha: str,
    token: str,
):
    source = _commit(repository, source_sha, token)
    qualified = _commit(repository, qualified_source_sha, token)

    source_tree = (source.get("tree") or {}).get("sha")
    qualified_tree = (qualified.get("tree") or {}).get("sha")
    if not source_tree or source_tree != qualified_tree:
        raise ValueError(
            "permanent source tree differs from qualified PR merge tree"
        )

    parents = [
        parent.get("sha")
        for parent in qualified.get("parents", [])
        if isinstance(parent, dict)
    ]
    if parents != [base_sha, head_sha]:
        raise ValueError(
            "qualification artifact source is not the reviewed PR merge tree"
        )


def _rebind_plan(
    candidate: Path,
    *,
    source_sha: str,
    qualified_source_sha: str,
    qualified_head_sha: str,
    pr_number: int,
    run_id: int,
):
    path = candidate / "build-plan.json"
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            "qualification artifact has no valid build-plan.json"
        ) from exc
    if (
        plan.get("schema") != 2
        or plan.get("source_sha") != qualified_source_sha
    ):
        raise ValueError("qualification artifact provenance mismatch")

    plan["source_sha"] = source_sha
    plan["qualified_source_sha"] = qualified_source_sha
    plan["qualified_head_sha"] = qualified_head_sha
    plan["qualification_reused"] = True
    plan["qualification_pr"] = pr_number
    plan["qualification_run_id"] = run_id
    path.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def materialize(
    *,
    repo: Path,
    repository: str,
    branch: str,
    source_sha: str,
    token: str,
    candidate: Path,
    pr_number: int | None = None,
    head_sha: str = "",
    run_id: int | None = None,
) -> dict:
    project = load_project(repo)
    if branch not in project.reuse_pr_branches:
        return {"reuse": False, "reason": "branch-not-configured"}
    bound = (
        type(pr_number) is int
        and type(run_id) is int
        and isinstance(head_sha, str)
        and bool(head_sha)
    )
    if bound:
        evidence = reusable_pr_qualification(
            repository=repository,
            branch=branch,
            token=token,
            source_sha=source_sha,
            pr_number=pr_number,
            head_sha=head_sha,
            run_id=run_id,
        )
        if evidence is None:
            return {"reuse": False, "reason": "invalid-merge-policy-binding"}
        reuse_reason = "merge-policy-bound-green-pr"
    else:
        evidence = discover_reusable_pr_qualification(
            repository=repository,
            branch=branch,
            token=token,
            source_sha=source_sha,
        )
        if evidence is None:
            return {"reuse": False, "reason": "no-reusable-pr-evidence"}
        reuse_reason = "discovered-tree-identical-green-pr"

    shutil.rmtree(candidate, ignore_errors=True)
    data = _download_artifact(repository, evidence.artifact_id, token)
    _extract_zip(data, candidate)

    qualified_source_sha = _artifact_source(candidate)
    _require_same_qualified_tree(
        repository=repository,
        source_sha=source_sha,
        qualified_source_sha=qualified_source_sha,
        base_sha=evidence.base_sha,
        head_sha=evidence.head_sha,
        token=token,
    )
    _rebind_plan(
        candidate,
        source_sha=source_sha,
        qualified_source_sha=qualified_source_sha,
        qualified_head_sha=evidence.head_sha,
        pr_number=evidence.pr_number,
        run_id=evidence.run_id,
    )
    return {
        "reuse": True,
        "reason": reuse_reason,
        "qualified_source_sha": qualified_source_sha,
        "qualified_head_sha": evidence.head_sha,
        "pr_number": evidence.pr_number,
        "run_id": evidence.run_id,
    }


def _optional_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--qualification-pr", default="")
    parser.add_argument("--qualification-head-sha", default="")
    parser.add_argument("--qualification-run-id", default="")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        _write_output(
            args.github_output,
            reuse="false",
            reason="missing-token",
        )
        return

    try:
        result = materialize(
            repo=args.repo,
            repository=args.repository,
            branch=args.branch,
            source_sha=args.source_sha,
            token=token,
            candidate=args.candidate,
            pr_number=_optional_int(args.qualification_pr),
            head_sha=args.qualification_head_sha,
            run_id=_optional_int(args.qualification_run_id),
        )
    except ConfigError:
        raise
    except (
        error.URLError,
        OSError,
        ValueError,
        KeyError,
        zipfile.BadZipFile,
    ) as exc:
        shutil.rmtree(args.candidate, ignore_errors=True)
        _write_output(
            args.github_output,
            reuse="false",
            reason="reuse-fallback",
        )
        print(f"Reusable PR qualification unavailable: {exc}")
        return

    values = {
        "reuse": "true" if result["reuse"] else "false",
        "reason": result["reason"],
    }
    if result["reuse"]:
        values.update(
            qualified_source_sha=result["qualified_source_sha"],
            qualified_head_sha=result["qualified_head_sha"],
            pr_number=result["pr_number"],
            run_id=result["run_id"],
        )
    _write_output(args.github_output, **values)


if __name__ == "__main__":
    main()
