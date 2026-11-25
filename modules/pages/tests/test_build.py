from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from cad_library_pages.build import build

class BuildTests(unittest.TestCase):
    def test_build_invokes_hugo_and_requires_index(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "site").mkdir()
            (root / "cadlib/src/scpf").mkdir(parents=True)
            (root / "cadlib/pyproject.toml").write_text(
                '[project]\nname = "scpf"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            (root / "cadlib/src/scpf/version.py").write_text(
                'TESTED_SOLIDCRAFT_VERSION = "9.8.7"\n',
                encoding="utf-8",
            )
            destination = root / "out"
            destination.mkdir()
            with patch("cad_library_pages.build.subprocess.run") as run:
                with self.assertRaises(RuntimeError):
                    build(source_root=root, destination=destination, base_url="https://example.org/dev/")
                (destination / "index.html").touch()
                build(source_root=root, destination=destination, base_url="https://example.org/dev/")
                self.assertIn("https://example.org/dev/", run.call_args.args[0])
