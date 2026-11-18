"""Tests for the pinned external tool.cad.ci manifest parser."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import bootstrap_cad_ci


class BootstrapCadCiTests(unittest.TestCase):
    def test_dependency_requires_exact_commit(self):
        """The bootstrap parser returns the exact configured Git revision."""

        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "dependencies.repos").write_text(
                "repositories:\n"
                "  cad-ci:\n"
                "    type: git\n"
                "    url: https://example.invalid/tool.cad.ci.git\n"
                "    version: 0123456789abcdef0123456789abcdef01234567\n",
                encoding="utf-8",
            )
            self.assertEqual(
                bootstrap_cad_ci.dependency(root),
                (
                    "https://example.invalid/tool.cad.ci.git",
                    "0123456789abcdef0123456789abcdef01234567",
                ),
            )

    def test_dependency_rejects_moving_version_name(self):
        """A branch or tag name is not a reproducible consumer pin."""

        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "dependencies.repos").write_text(
                "repositories:\n"
                "  cad-ci:\n"
                "    type: git\n"
                "    url: https://example.invalid/tool.cad.ci.git\n"
                "    version: main\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "exact commit SHA",
            ):
                bootstrap_cad_ci.dependency(root)


if __name__ == "__main__":
    unittest.main()
