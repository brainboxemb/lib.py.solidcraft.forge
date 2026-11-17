"""Release validation must stop on explicit foundational blockers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release" / "validate_release.py"

spec = spec_from_file_location("scpf_release_validation", SCRIPT)
release_validation = module_from_spec(spec)
spec.loader.exec_module(release_validation)


class ReleaseValidationTests(unittest.TestCase):
    def test_repository_has_no_active_release_blocker_after_completed_audit(self):
        blocker_file = ROOT / release_validation.BLOCKERS_PATH
        self.assertEqual(
            release_validation.active_blockers(
                blocker_file.read_text(encoding="utf-8")
            ),
            (),
        )

    def test_comments_only_blocker_file_has_no_active_blockers(self):
        self.assertEqual(
            release_validation.active_blockers(
                "# release blockers\n\n# none active\n"
            ),
            (),
        )

    def test_active_blocker_stops_release_and_names_reason(self):
        target = "a" * 40
        with (
            patch.object(release_validation, "git", return_value=target),
            patch.object(
                release_validation,
                "read_at",
                return_value=(
                    "# release blockers\n"
                    "rotated normal attachments are not safe yet\n"
                ),
            ),
            tempfile.TemporaryDirectory() as directory,
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "rotated normal attachments are not safe yet",
            ):
                release_validation.validate(
                    "0.3.5",
                    target,
                    Path(directory) / "notes.md",
                )

    def test_comments_only_blocker_file_allows_normal_release_validation(self):
        target = "b" * 40
        version = "0.3.5"
        files = {
            release_validation.BLOCKERS_PATH: "# no active blockers\n",
            "scpf/pyproject.toml": (
                "[project]\n"
                f'name = "scpf"\nversion = "{version}"\n'
            ),
            "CHANGELOG.md": (
                "# Changelog\n\n"
                f"## [{version}] - 2026-11-16\n\n"
                "- qualification cleanup\n"
            ),
            "scpf/scpf/version.py": (
                "TESTED_SOLIDCRAFT_VERSION = "
                f'"{TESTED_SOLIDCRAFT_VERSION}"\n'
            ),
        }

        def read_at(_commit, path):
            return files[path]

        with (
            patch.object(release_validation, "git", return_value=target),
            patch.object(release_validation, "read_at", side_effect=read_at),
            tempfile.TemporaryDirectory() as directory,
        ):
            notes = Path(directory) / "notes.md"
            solidcraft = release_validation.validate(
                version,
                target,
                notes,
            )
            note_text = notes.read_text(encoding="utf-8")

        self.assertEqual(solidcraft, TESTED_SOLIDCRAFT_VERSION)
        self.assertIn(f"## [{version}]", note_text)


if __name__ == "__main__":
    unittest.main()
