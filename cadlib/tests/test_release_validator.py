"""Tests for Forge-owned release metadata validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
import tomllib
import unittest


MODULE_PATH = Path("cadlib/release.py").resolve()
SPEC = importlib.util.spec_from_file_location("forge_release", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)

TARGET = "a" * 40


def package_version() -> str:
    data = tomllib.loads(
        Path("cadlib/pyproject.toml").read_text(encoding="utf-8")
    )
    return str(data["project"]["version"])


def tested_solidcraft_version() -> str:
    source = Path("cadlib/src/scpf/version.py").read_text(encoding="utf-8")
    match = re.search(
        r'^TESTED_SOLIDCRAFT_VERSION = "([^"]+)"$',
        source,
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError("cannot read TESTED_SOLIDCRAFT_VERSION")
    return match.group(1)


def write_candidate(
    root: Path,
    *,
    package_version_value: str | None = None,
    blockers: str = "",
    changelog_version: str | None = None,
    solidcraft_version: str | None = None,
):
    version = package_version_value or package_version()
    changelog = changelog_version or version
    solidcraft = solidcraft_version or tested_solidcraft_version()

    (root / "docs/background/design").mkdir(parents=True)
    (root / "docs/background/design/release-blockers.txt").write_text(
        blockers or "# no active blockers\n",
        encoding="utf-8",
    )
    (root / "cadlib/src/scpf").mkdir(parents=True)
    (root / "cadlib/pyproject.toml").write_text(
        '[project]\nname = "scpf"\n'
        f'version = "{version}"\n',
        encoding="utf-8",
    )
    (root / "cadlib/src/scpf/version.py").write_text(
        f'TESTED_SOLIDCRAFT_VERSION = "{solidcraft}"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        f"## [{changelog}] - 2026-11-25\n\n"
        "### Added\n\n- release candidate\n\n"
        "## [0.15.0] - 2026-11-24\n\n"
        "### Changed\n\n- migrated historical baseline\n",
        encoding="utf-8",
    )


class ForgeReleaseValidatorTests(unittest.TestCase):
    def run_validate(self, *, requested_version: str | None = None, **candidate):
        requested = requested_version or package_version()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(root, **candidate)
            notes = root / "notes.md"
            solidcraft = validator.validate(
                requested,
                TARGET,
                notes,
                root=root,
            )
            return solidcraft, notes.read_text(encoding="utf-8")

    def test_accepts_current_branch_release_metadata(self):
        version = package_version()
        solidcraft, notes = self.run_validate()
        self.assertEqual(solidcraft, tested_solidcraft_version())
        self.assertIn(f"## [{version}] - 2026-11-25", notes)
        self.assertNotIn("## [0.15.0]", notes)

    def test_rejects_migrated_baseline_as_new_release(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(
                root,
                package_version_value="0.15.0",
                changelog_version="0.15.0",
            )
            with self.assertRaisesRegex(SystemExit, "newer than migrated"):
                validator.validate("0.15.0", TARGET, root / "notes.md", root=root)

    def test_rejects_older_release_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(
                root,
                package_version_value="0.14.0",
                changelog_version="0.14.0",
            )
            with self.assertRaisesRegex(SystemExit, "newer than migrated"):
                validator.validate("0.14.0", TARGET, root / "notes.md", root=root)

    def test_rejects_package_version_mismatch(self):
        mismatch = "999.0.0" if package_version() != "999.0.0" else "998.0.0"
        with self.assertRaisesRegex(SystemExit, "package version mismatch"):
            self.run_validate(requested_version=mismatch)

    def test_rejects_active_release_blocker(self):
        with self.assertRaisesRegex(SystemExit, "release blocked"):
            self.run_validate(blockers="owner issue still open\n")

    def test_rejects_missing_dated_release_section(self):
        version = package_version()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(root)
            (root / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [Unreleased]\n\n"
                "### Added\n- work\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "no dated"):
                validator.validate(
                    version,
                    TARGET,
                    root / "notes.md",
                    root=root,
                )

    def test_rejects_invalid_target_sha(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(root)
            with self.assertRaisesRegex(SystemExit, "40 lowercase"):
                validator.validate(
                    package_version(),
                    "not-a-sha",
                    root / "notes.md",
                    root=root,
                )

    def test_validator_owns_no_build_pages_or_publication_mechanics(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("origin/build", source)
        self.assertNotIn("gh-pages", source)
        self.assertNotIn("git tag", source)
        self.assertNotIn("gh release", source)
        self.assertNotIn("subprocess", source)


if __name__ == "__main__":
    unittest.main()
