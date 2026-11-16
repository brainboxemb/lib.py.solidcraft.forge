"""Validate SCPF release metadata before publishing a Git tag/release."""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path

SEMVER = re.compile(r"\d+\.\d+\.\d+")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
BLOCKERS_PATH = "docs/design/release-blockers.txt"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def read_at(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def active_blockers(text: str) -> tuple[str, ...]:
    """Return non-comment release blocker lines."""
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def validate(version: str, target_sha: str, notes_out: Path) -> str:
    if SEMVER.fullmatch(version) is None:
        raise SystemExit("version must be plain SemVer, for example 0.2.0")
    if FULL_SHA.fullmatch(target_sha) is None:
        raise SystemExit("target_sha must be a full 40-character commit SHA")

    main_sha = git("rev-parse", "origin/main")
    if target_sha != main_sha:
        raise SystemExit(
            f"release target must equal current main HEAD: {main_sha}"
        )

    blockers = active_blockers(read_at(target_sha, BLOCKERS_PATH))
    if blockers:
        detail = "\n".join(f"- {blocker}" for blocker in blockers)
        raise SystemExit(
            "release blocked by foundational Forge issue(s):\n" + detail
        )

    pyproject = tomllib.loads(read_at(target_sha, "scpf/pyproject.toml"))
    package_version = pyproject["project"]["version"]
    if package_version != version:
        raise SystemExit(
            f"package version mismatch: expected {version}, found {package_version}"
        )

    changelog = read_at(target_sha, "CHANGELOG.md")
    heading = re.compile(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        re.MULTILINE,
    )
    match = heading.search(changelog)
    if match is None:
        raise SystemExit(f"CHANGELOG.md has no dated [{version}] section")

    version_source = read_at(target_sha, "scpf/scpf/version.py")
    solidcraft = re.search(
        r'^TESTED_SOLIDCRAFT_VERSION = "([^"]+)"$',
        version_source,
        re.MULTILINE,
    )
    if solidcraft is None:
        raise SystemExit("cannot read TESTED_SOLIDCRAFT_VERSION")

    next_section = changelog.find("\n## [", match.end())
    if next_section < 0:
        next_section = len(changelog)
    notes_out.write_text(
        changelog[match.start():next_section].strip() + "\n",
        encoding="utf-8",
    )
    return solidcraft.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--notes-out", type=Path, default=Path("release-notes.md"))
    args = parser.parse_args()

    solidcraft = validate(args.version, args.target_sha, args.notes_out)
    print(f"SCPF {args.version}; qualified SolidCraft {solidcraft}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
