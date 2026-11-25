"""Validate one release source against retained full stable CAD evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from .delta import ReleaseDeltaError, validate_metadata_delta


_SHA = re.compile(r"^[0-9a-f]{40}$")


class ReleaseQualificationError(RuntimeError):
    """Stable durable evidence does not qualify the requested release source."""


def _exact_sha(value: str, label: str) -> str:
    value = value.strip().lower()
    if _SHA.fullmatch(value) is None:
        raise ReleaseQualificationError(
            f"{label} must be exactly 40 lowercase hex characters"
        )
    return value


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise ReleaseQualificationError(f"missing release evidence: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseQualificationError(f"invalid release evidence: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseQualificationError(f"release evidence is not an object: {path}")
    return value


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def validate_build_scope(build_scope: Path, source_sha: str) -> dict:
    """Require one complete durable stable build for its exact product source."""

    build_scope = build_scope.resolve()
    source_sha = _exact_sha(source_sha, "source_sha")

    plan = _read_json(build_scope / "build-plan.json")
    if plan.get("schema") != 2:
        raise ReleaseQualificationError("unsupported build-plan schema")
    if plan.get("source_sha") != source_sha:
        raise ReleaseQualificationError("stable build source does not match release source")
    if plan.get("full") is not True:
        raise ReleaseQualificationError("release requires a full stable build")
    if plan.get("library") is not True:
        raise ReleaseQualificationError("stable build did not qualify the library")

    active = plan.get("active")
    selected = plan.get("selected")
    if not isinstance(active, list) or not all(isinstance(item, str) for item in active):
        raise ReleaseQualificationError("build plan has invalid active model owners")
    if not isinstance(selected, list) or selected != active:
        raise ReleaseQualificationError(
            "release requires every active model owner to be selected"
        )

    rows = plan.get("models")
    if not isinstance(rows, list):
        raise ReleaseQualificationError("build plan has invalid model rows")
    row_ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != len(rows) or row_ids != active:
        raise ReleaseQualificationError(
            "build plan model rows do not match active owners"
        )

    for owner in active:
        root = build_scope / "models" / owner
        result = _read_json(root / "result.json")
        if result.get("id") != owner or result.get("status") != "pass":
            raise ReleaseQualificationError(f"model is not successful: {owner}")
        provenance = _read_json(root / "source.json")
        if provenance.get("source_sha") != source_sha:
            raise ReleaseQualificationError(
                f"model source does not match release source: {owner}"
            )

    return plan


def release_metadata_delta(
    source_root: Path,
    product_sha: str,
    release_sha: str,
) -> tuple[str, ...]:
    """Validate a linear stable history containing release metadata only."""

    source_root = source_root.resolve()
    product_sha = _exact_sha(product_sha, "product source SHA")
    release_sha = _exact_sha(release_sha, "release source SHA")
    if product_sha == release_sha:
        return ()

    ancestor = _git(
        source_root,
        "merge-base",
        "--is-ancestor",
        product_sha,
        release_sha,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ReleaseQualificationError(
            "durable product source is not an ancestor of release source"
        )

    commits = tuple(
        line.strip()
        for line in _git(
            source_root,
            "rev-list",
            "--first-parent",
            "--reverse",
            f"{product_sha}..{release_sha}",
        ).stdout.splitlines()
        if line.strip()
    )
    if not commits:
        raise ReleaseQualificationError(
            "release source is not on the product source first-parent history"
        )

    previous = product_sha
    changed: list[str] = []
    for commit in commits:
        parts = _git(
            source_root,
            "rev-list",
            "--parents",
            "-n",
            "1",
            commit,
        ).stdout.strip().split()
        if len(parts) != 2 or parts[1] != previous:
            raise ReleaseQualificationError(
                "release metadata history must be linear and single-parent"
            )

        try:
            paths = validate_metadata_delta(source_root, previous, commit)
        except ReleaseDeltaError as exc:
            raise ReleaseQualificationError(str(exc)) from exc
        changed.extend(paths)
        previous = commit

    if previous != release_sha:
        raise ReleaseQualificationError(
            "release source is not on the product source first-parent history"
        )
    return tuple(dict.fromkeys(changed))


def validate_release_source(
    build_scope: Path,
    source_root: Path,
    release_sha: str,
) -> tuple[dict, tuple[str, ...]]:
    """Qualify exact main release SHA from full product evidence plus safe metadata."""

    release_sha = _exact_sha(release_sha, "release source SHA")
    source_root = source_root.resolve()
    head = _exact_sha(
        _git(source_root, "rev-parse", "HEAD").stdout.strip(),
        "checked-out release source",
    )
    if head != release_sha:
        raise ReleaseQualificationError(
            "checked-out release source does not match requested release SHA"
        )

    plan = _read_json(build_scope.resolve() / "build-plan.json")
    product_sha = _exact_sha(str(plan.get("source_sha") or ""), "product source SHA")
    validate_build_scope(build_scope, product_sha)

    paths = release_metadata_delta(source_root, product_sha, release_sha)
    return plan, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-scope", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    plan, paths = validate_release_source(
        args.build_scope,
        args.source_root,
        args.source_sha,
    )
    product_sha = plan["source_sha"]
    if product_sha == args.source_sha:
        print(f"qualified exact full stable CAD-library build {args.source_sha}")
    else:
        detail = ", ".join(paths)
        print(
            "qualified release metadata source "
            f"{args.source_sha} from full product baseline {product_sha}: {detail}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
