"""SolidCraft version compatibility guards should not silently accept older engines."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import warnings
from unittest.mock import patch
from scpf.version import (
    TESTED_SOLIDCRAFT_VERSION,
    check_cli_version,
    forge_revision,
    package_version,
    parse_version,
    validate_version,
)


class NativeVersionTests(unittest.TestCase):
    def test_package_version_uses_distribution_metadata(self):
        with patch("scpf.version.metadata.version", return_value="0.11.0") as version:
            self.assertEqual(package_version(), "0.11.0")
        version.assert_called_once_with("scpf")

    def test_checkout_revision_is_reported_only_as_full_git_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            with patch("scpf.version.subprocess.run") as run:
                run.return_value.stdout = ("b" * 40) + "\n"
                self.assertEqual(forge_revision(root / "scpf"), "b" * 40)
            run.assert_called_once_with(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=2,
            )

            with patch("scpf.version.subprocess.run") as run:
                run.return_value.stdout = "not-a-sha\n"
                self.assertIsNone(forge_revision(root))

    def test_checkout_revision_is_optional_without_git_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(forge_revision(Path(tmp)))

    def test_parse_cli_banner(self):
        self.assertEqual(parse_version("solidcraft-cli 0.30.1"), (0, 30, 1))
        self.assertEqual(parse_version("SolidCraft v0.31.0\n"), (0, 31, 0))
        with self.assertRaises(ValueError):
            parse_version("unrecognized banner")

    def test_tested_version_is_supported(self):
        with warnings.catch_warnings(record=True) as notes:
            warnings.simplefilter("always")
            self.assertEqual(
                validate_version(f"SolidCraft {TESTED_SOLIDCRAFT_VERSION}"),
                parse_version(TESTED_SOLIDCRAFT_VERSION),
            )
            self.assertEqual(notes, [])

    def test_older_engine_is_rejected(self):
        major, minor, _patch = parse_version(TESTED_SOLIDCRAFT_VERSION)
        older = f"{major}.{minor - 1}.0"
        with self.assertRaisesRegex(RuntimeError, "too old"):
            validate_version(f"solidcraft-cli {older}")

    def test_newer_engine_warns(self):
        major, minor, _patch = parse_version(TESTED_SOLIDCRAFT_VERSION)
        newer = f"{major}.{minor + 1}.0"
        with self.assertWarnsRegex(RuntimeWarning, "differs from tested"):
            self.assertEqual(
                validate_version(f"SolidCraft {newer}"),
                parse_version(newer),
            )

    def test_no_cli_warns_in_gui_mode(self):
        with patch("scpf.version.shutil.which", return_value=None):
            with self.assertWarnsRegex(RuntimeWarning, "cannot verify"):
                self.assertIsNone(check_cli_version())
            with self.assertRaisesRegex(RuntimeError, "not found"):
                check_cli_version(require_cli=True)

    def test_detect_cli_version_from_subprocess(self):
        with patch("scpf.version.shutil.which", return_value="/fake/solidcraft-cli"):
            with patch("scpf.version.subprocess.run") as run:
                run.return_value.stdout = (
                    f"solidcraft-cli {TESTED_SOLIDCRAFT_VERSION}\n"
                )
                run.return_value.stderr = ""
                self.assertEqual(
                    check_cli_version(require_cli=True),
                    parse_version(TESTED_SOLIDCRAFT_VERSION),
                )
                run.assert_called_once()
