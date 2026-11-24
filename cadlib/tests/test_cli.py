from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scpf.__main__ import main
from scpf.compiler import ModelError


class CliPresentationTests(unittest.TestCase):
    def test_version_works_without_model_or_native_runtime(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("scpf.__main__.package_version", return_value="0.11.0"):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as stopped:
                    main(["--version"])
        self.assertEqual(stopped.exception.code, 0)
        self.assertIn("SCPF 0.11.0", stdout.getvalue() + stderr.getvalue())

    def test_model_build_error_is_concise_and_reports_source_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "broken_model.py"
            model.write_text(
                "def Broken():\n"
                "    raise ValueError('bad model input')\n"
                "Broken()\n",
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with patch("scpf.__main__.package_version", return_value="0.11.0"):
                with redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as stopped:
                        main([str(model), "--out", str(root / "out.json")])

            text = stderr.getvalue()
            self.assertEqual(stopped.exception.code, 1)
            self.assertIn("SCPF 0.11.0 error", text)
            self.assertIn(str(model), text)
            self.assertIn(":2", text)
            self.assertIn("ValueError: bad model input", text)
            self.assertIn("--debug", text)
            self.assertNotIn("Traceback", text)

    def test_compiler_error_uses_same_concise_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.py"
            stderr = io.StringIO()
            with (
                patch(
                    "scpf.__main__.run_script",
                    side_effect=ModelError("compiler contract failed"),
                ),
                patch("scpf.__main__.package_version", return_value="0.11.0"),
                redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as stopped:
                    main([str(model), "--out", str(root / "out.json")])

            text = stderr.getvalue()
            self.assertEqual(stopped.exception.code, 1)
            self.assertIn("ModelError: compiler contract failed", text)
            self.assertIn(str(model.resolve()), text)
            self.assertNotIn("Traceback", text)

    def test_debug_mode_keeps_original_exception_and_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.py"
            stderr = io.StringIO()
            with (
                patch(
                    "scpf.__main__.run_script",
                    side_effect=ModelError("debug compiler failure"),
                ),
                patch("scpf.__main__.package_version", return_value="0.11.0"),
                patch("scpf.__main__.forge_revision", return_value="a" * 40),
                redirect_stderr(stderr),
            ):
                with self.assertRaisesRegex(
                    ModelError,
                    "debug compiler failure",
                ):
                    main(
                        [
                            str(model),
                            "--out",
                            str(root / "out.json"),
                            "--debug",
                        ]
                    )

            text = stderr.getvalue()
            self.assertIn("SCPF 0.11.0", text)
            self.assertIn("Forge revision: " + ("a" * 40), text)
            self.assertIn("Tested SolidCraft:", text)

    def test_debug_cli_process_emits_python_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "broken_model.py"
            model.write_text(
                "def Broken():\n"
                "    raise ValueError('trace me')\n"
                "Broken()\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scpf",
                    str(model),
                    "--out",
                    str(root / "out.json"),
                    "--debug",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Traceback (most recent call last)", completed.stderr)
            self.assertIn("ValueError: trace me", completed.stderr)


if __name__ == "__main__":
    unittest.main()
