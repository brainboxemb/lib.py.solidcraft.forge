"""Validate the narrow release-metadata delta."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import subprocess
import tomllib


RELEASE_METADATA_PATHS = frozenset({
    "CHANGELOG.md",
    "cadlib/pyproject.toml",
})


class ReleaseDeltaError(RuntimeError):
    """A candidate release changes product or non-release metadata."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _show(repo: Path, ref: str, path: str) -> str:
    result = _git(repo, "show", f"{ref}:{path}", check=False)
    if result.returncode != 0:
        raise ReleaseDeltaError(f"release metadata path is missing at {ref}: {path}")
    return result.stdout


def _without_project_version(raw: str) -> tuple[dict, str]:
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise ReleaseDeltaError("cadlib/pyproject.toml is invalid TOML") from exc
    project = data.get("project")
    if not isinstance(project, dict) or not isinstance(project.get("version"), str):
        raise ReleaseDeltaError(
            "cadlib/pyproject.toml must contain string project.version"
        )
    version = project["version"]
    normalized = deepcopy(data)
    normalized["project"]["version"] = "<release-version>"
    return normalized, version


def validate_metadata_delta(
    source_root: Path,
    base_ref: str,
    target_ref: str,
) -> tuple[str, ...]:
    """Require changelog and/or a project.version-only pyproject change."""

    source_root = source_root.resolve()
    result = _git(
        source_root,
        "diff",
        "--name-only",
        base_ref,
        target_ref,
        "--",
    )
    paths = tuple(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    )
    if not paths:
        raise ReleaseDeltaError("release metadata delta is empty")

    unexpected = sorted(set(paths) - RELEASE_METADATA_PATHS)
    if unexpected:
        raise ReleaseDeltaError(
            "release changes product/non-release path(s): " + ", ".join(unexpected)
        )

    if "cadlib/pyproject.toml" in paths:
        before, old_version = _without_project_version(
            _show(source_root, base_ref, "cadlib/pyproject.toml")
        )
        after, new_version = _without_project_version(
            _show(source_root, target_ref, "cadlib/pyproject.toml")
        )
        if before != after:
            raise ReleaseDeltaError(
                "cadlib/pyproject.toml changes more than project.version"
            )
        if old_version == new_version:
            raise ReleaseDeltaError(
                "cadlib/pyproject.toml changed without changing project.version"
            )

    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--target-ref", required=True)
    args = parser.parse_args()

    paths = validate_metadata_delta(
        args.source_root,
        args.base_ref,
        args.target_ref,
    )
    print("qualified release metadata delta: " + ", ".join(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
