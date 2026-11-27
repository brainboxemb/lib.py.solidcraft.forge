from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from cad_library_solidcraft_reference import __main__ as cli


class SolidCraftReferenceCliTests(unittest.TestCase):
    def test_capture_describe_keeps_subcommand_separate_from_command_option(self):
        snapshot = Path("config.rule.json")
        argv = [
            "cad_library_solidcraft_reference",
            "capture-describe",
            "--image", "example/runtime:v1",
            "--version", "0.50.0",
            "--command", "config.rule",
            "--snapshot", str(snapshot),
        ]
        with (
            patch.object(sys, "argv", argv),
            patch.object(cli, "capture_describe_snapshot") as capture,
        ):
            self.assertEqual(cli.main(), 0)

        capture.assert_called_once_with(
            image="example/runtime:v1",
            version="0.50.0",
            command="config.rule",
            snapshot=snapshot,
        )

    def test_verify_describe_keeps_subcommand_separate_from_command_option(self):
        snapshot = Path("config.rule.json")
        argv = [
            "cad_library_solidcraft_reference",
            "verify-describe",
            "--image", "example/runtime:v1",
            "--version", "0.50.0",
            "--command", "config.rule",
            "--snapshot", str(snapshot),
        ]
        with (
            patch.object(sys, "argv", argv),
            patch.object(cli, "verify_describe_snapshot") as verify,
        ):
            self.assertEqual(cli.main(), 0)

        verify.assert_called_once_with(
            image="example/runtime:v1",
            version="0.50.0",
            command="config.rule",
            snapshot=snapshot,
        )


if __name__ == "__main__":
    unittest.main()
