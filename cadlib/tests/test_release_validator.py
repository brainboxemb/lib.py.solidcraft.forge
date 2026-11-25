"""Tests for Forge-owned release validation in the canonical repository."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path("cadlib/release.py").resolve()
SPEC = importlib.util.spec_from_file_location("forge_release", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)

TARGET = "a" * 40


def write_candidate(
    root: Path,
    *,
    package_version: str = "0.16.0",
    blockers: str = "",
    changelog_version: str = "0.16.0",
):
    (root / "docs/background/design").mkdir(parents=True)
    (root / "docs/background/design/release-blockers.txt").write_text(
        blockers or "# no active blockers\n",
        encoding="utf-8",
    )
    (root / "cadlib/src/scpf").mkdir(parents=True)
    (root / "cadlib/pyproject.toml").write_text(
        '[project]\nname = "scpf"\n'
        f'version = "{package_version}"\n',
        encoding="utf-8",
    )
    (root / "cadlib/src/scpf/version.py").write_text(
        'TESTED_SOLIDCRAFT_VERSION = "0.49.0"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        f"## [{changelog_version}] - 2026-11-25\n\n"
        "### Added\n\n- canonical release candidate\n\n"
        "## [0.15.0] - 2026-11-24\n\n"
        "### Changed\n\n- migrated historical baseline\n",
        encoding="utf-8",
    )


class ForgeNewReleaseValidatorTests(unittest.TestCase):
    def run_validate(self, **candidate):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(root, **candidate)
            notes = root / "notes.md"
            solidcraft = validator.validate(
                "0.16.0",
                TARGET,
                notes,
                root=root,
            )
            return solidcraft, notes.read_text(encoding="utf-8")

    def test_accepts_first_canonical_release_metadata(self):
        solidcraft, notes = self.run_validate()
        self.assertEqual(solidcraft, "0.49.0")
        self.assertIn("## [0.16.0] - 2026-11-25", notes)
        self.assertNotIn("## [0.15.0]", notes)

    def test_rejects_migrated_baseline_as_new_release(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(
                root,
                package_version="0.15.0",
                changelog_version="0.15.0",
            )
            with self.assertRaisesRegex(SystemExit, "newer than migrated"):
                validator.validate("0.15.0", TARGET, root / "notes.md", root=root)

    def test_rejects_older_release_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_candidate(
                root,
                package_version="0.14.0",
                changelog_version="0.14.0",
            )
            with self.assertRaisesRegex(SystemExit, "newer than migrated"):
                validator.validate("0.14.0", TARGET, root / "notes.md", root=root)

    def test_rejects_package_version_mismatch(self):
        with self.assertRaisesRegex(SystemExit, "package version mismatch"):
            self.run_validate(package_version="0.15.0")

    def test_rejects_active_release_blocker(self):
        with self.assertRaisesRegex(SystemExit, "release blocked"):
            self.run_validate(blockers="owner issue still open\n")

    def test_rejects_missing_dated_release_section(self):
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
                    "0.16.0",
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
                    "0.16.0",
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
