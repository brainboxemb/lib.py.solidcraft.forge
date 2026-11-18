#!/usr/bin/env python3
"""Create one SCPF release after a fully qualified Forge run."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=not check,
    )


def release(*, target_sha: str, build_sha: str) -> bool:
    version = tomllib.loads(
        (ROOT / "scpf/pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    tag = f"v{version}"

    existing = run(
        ["gh", "release", "view", tag, "--repo", "brainboxemb/lib.py.solidcraft.forge"],
        check=False,
    )
    if existing.returncode == 0:
        print(f"{tag} already exists; no release needed")
        return False

    run([
        sys.executable,
        "scripts/release/validate_release.py",
        "--version",
        version,
        "--target-sha",
        target_sha,
        "--notes-out",
        "release-notes.md",
    ])

    run(["git", "fetch", "origin", "--tags"])
    tag_exists = run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"], check=False)
    if tag_exists.returncode == 0:
        current = subprocess.check_output(
            ["git", "rev-list", "-n", "1", tag],
            cwd=ROOT,
            text=True,
        ).strip()
        if current != target_sha:
            raise RuntimeError(f"{tag} points to {current}, not {target_sha}")
    else:
        run(["git", "config", "user.name", "github-actions[bot]"])
        run([
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ])
        run(["git", "tag", "-a", tag, target_sha, "-m", f"SCPF {tag}"])
        run(["git", "push", "origin", tag])

    evidence_tag = f"evidence/{tag}"
    run(["git", "fetch", "origin", "build", "--tags"])
    evidence_exists = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{evidence_tag}"],
        check=False,
    )
    if evidence_exists.returncode == 0:
        current = subprocess.check_output(
            ["git", "rev-list", "-n", "1", evidence_tag],
            cwd=ROOT,
            text=True,
        ).strip()
        if current != build_sha:
            raise RuntimeError(
                f"{evidence_tag} points to {current}, not {build_sha}"
            )
    else:
        run([
            "git",
            "tag",
            "-a",
            evidence_tag,
            build_sha,
            "-m",
            f"SCPF {tag} evidence",
        ])
        run(["git", "push", "origin", evidence_tag])

    run([
        "gh",
        "release",
        "create",
        tag,
        "--repo",
        "brainboxemb/lib.py.solidcraft.forge",
        "--verify-tag",
        "--title",
        f"SCPF {tag}",
        "--notes-file",
        "release-notes.md",
    ])
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--build-sha", required=True)
    args = parser.parse_args()
    release(target_sha=args.target_sha, build_sha=args.build_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
