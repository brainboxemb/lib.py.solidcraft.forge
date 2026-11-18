#!/usr/bin/env python3
"""Publish an already-qualified Forge release.

This command is intentionally runnable outside GitHub Actions. CI provides
credentials and the qualified source/evidence SHAs; release policy and tagging
live here.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release.validate_release import validate


def run(args: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def output(args: list[str]) -> str:
    return run(args, capture=True).stdout.strip()


def version() -> str:
    with (ROOT / "scpf" / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def tag_target(tag: str) -> str | None:
    completed = run(
        ["git", "rev-list", "-n", "1", tag],
        capture=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def ensure_tag(tag: str, sha: str, message: str) -> None:
    current = tag_target(tag)
    if current:
        if current != sha:
            raise SystemExit(f"{tag} already points to {current}, expected {sha}")
        return
    run(["git", "tag", "-a", tag, sha, "-m", message])
    run(["git", "push", "origin", tag])


def release_exists(repository: str, tag: str) -> bool:
    completed = run(
        ["gh", "release", "view", tag, "--repo", repository],
        capture=True,
        check=False,
    )
    return completed.returncode == 0


def publish(*, repository: str, target_sha: str, build_sha: str) -> str:
    candidate = version()
    tag = f"v{candidate}"
    evidence_tag = f"evidence/{tag}"

    if release_exists(repository, tag):
        print(f"{tag} already released")
        return tag

    run(["git", "fetch", "origin", "main", "build", "--tags"])
    notes = ROOT / "release-notes.md"
    validate(candidate, target_sha, notes)

    run(["git", "config", "user.name", "github-actions[bot]"])
    run([
        "git",
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    ])

    ensure_tag(tag, target_sha, f"SCPF {tag}")
    ensure_tag(evidence_tag, build_sha, f"SCPF {tag} evidence")

    run([
        "gh", "release", "create", tag,
        "--repo", repository,
        "--verify-tag",
        "--title", f"SCPF {tag}",
        "--notes-file", str(notes),
    ])
    print(f"Published {tag}")
    return tag


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--build-sha", required=True)
    args = parser.parse_args()
    publish(
        repository=args.repository,
        target_sha=args.target_sha,
        build_sha=args.build_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
