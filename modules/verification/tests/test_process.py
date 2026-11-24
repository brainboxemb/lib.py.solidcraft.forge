"""Tests for external command execution semantics."""

from __future__ import annotations

import sys
import unittest

from cad_verification import CommandFailed, CommandTimedOut, run_command


class ProcessTests(unittest.TestCase):
    def test_success_captures_stdout_and_stderr(self):
        result = run_command(
            [
                sys.executable,
                "-c",
                "import sys; print('out'); print('err', file=sys.stderr)",
            ]
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "out")
        self.assertEqual(result.stderr.strip(), "err")

    def test_nonzero_exit_is_distinct(self):
        with self.assertRaises(CommandFailed) as caught:
            run_command(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('bad', file=sys.stderr); sys.exit(7)",
                ]
            )
        self.assertEqual(caught.exception.returncode, 7)
        self.assertIn("bad", caught.exception.stderr)

    def test_timeout_is_distinct(self):
        with self.assertRaises(CommandTimedOut):
            run_command(
                [
                    sys.executable,
                    "-c",
                    "import time; time.sleep(1)",
                ],
                timeout_seconds=0.05,
            )


if __name__ == "__main__":
    unittest.main()
