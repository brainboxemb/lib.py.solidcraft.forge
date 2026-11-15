"""SolidCraft version compatibility guards should not silently accept older engines."""
import unittest
import warnings
from unittest.mock import patch
from scpf.version import (parse_version, validate_version, check_cli_version,
                          TESTED_SOLIDCRAFT_VERSION)


class NativeVersionTests(unittest.TestCase):
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
