"""Forge-specific release metadata validation for the shared publisher."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import tomllib


BLOCKERS_PATH = Path("docs/background/design/release-blockers.txt")
MIGRATED_BASELINE_VERSION = (0, 15, 0)
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def parse_release_version(raw: str) -> tuple[int, int, int]:
    match = _SEMVER.fullmatch(str(raw).strip())
    if match is None:
        raise SystemExit(f"invalid release version: {raw!r}")
    return tuple(int(part) for part in match.groups())


def active_blockers(text: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def release_notes(changelog: str, version: str) -> str:
    unreleased = changelog.find("## [Unreleased]")
    if unreleased < 0:
        raise SystemExit("CHANGELOG.md has no [Unreleased] section")

    heading = re.compile(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        re.MULTILINE,
    )
    match = heading.search(changelog)
    if match is None:
        raise SystemExit(f"CHANGELOG.md has no dated [{version}] section")
    if match.start() < unreleased:
        raise SystemExit(f"[{version}] must follow the [Unreleased] section")

    next_heading = re.compile(r"^## \[", re.MULTILINE).search(
        changelog, match.end()
    )
    end = next_heading.start() if next_heading else len(changelog)
    notes = changelog[match.start():end].strip()
    if not re.search(r"^### ", notes, re.MULTILINE):
        raise SystemExit(
            f"CHANGELOG.md [{version}] section has no release content"
        )
    return notes + "\n"


def validate(
    version: str,
    target_sha: str,
    notes_out: Path,
    *,
    root: Path = Path("."),
) -> str:
    requested = parse_release_version(version)
    if requested <= MIGRATED_BASELINE_VERSION:
        raise SystemExit(
            "Forge NEW release version must be newer than migrated "
            "historical baseline 0.15.0"
        )
    if _SHA.fullmatch(target_sha) is None:
        raise SystemExit("target SHA must be exactly 40 lowercase hex characters")

    blockers = active_blockers(
        (root / BLOCKERS_PATH).read_text(encoding="utf-8")
    )
    if blockers:
        detail = "\n".join(f"- {blocker}" for blocker in blockers)
        raise SystemExit(
            "release blocked by foundational Forge issue(s):\n" + detail
        )

    pyproject = tomllib.loads(
        (root / "cadlib/pyproject.toml").read_text(encoding="utf-8")
    )
    package_version = str(pyproject["project"]["version"])
    if package_version != version:
        raise SystemExit(
            f"package version mismatch: expected {version}, "
            f"found {package_version}"
        )

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    notes_out.write_text(
        release_notes(changelog, version),
        encoding="utf-8",
    )

    version_source = (root / "cadlib/src/scpf/version.py").read_text(
        encoding="utf-8"
    )
    solidcraft = re.search(
        r'^TESTED_SOLIDCRAFT_VERSION = "([^"]+)"$',
        version_source,
        re.MULTILINE,
    )
    if solidcraft is None:
        raise SystemExit("cannot read TESTED_SOLIDCRAFT_VERSION")
    return solidcraft.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--notes-out", type=Path, required=True)
    args = parser.parse_args()

    solidcraft = validate(args.version, args.target_sha, args.notes_out)
    print(f"SCPF {args.version}; qualified SolidCraft {solidcraft}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
