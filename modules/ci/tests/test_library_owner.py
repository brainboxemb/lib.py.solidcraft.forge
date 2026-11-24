from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.config import load_build, full_selection, ConfigError
from cad_library_ci.selection import changed_selection
from cad_library_ci.library import library_owner, build_wheel


class LibraryOwnerTests(unittest.TestCase):
    def test_selection_is_independent(self):
        self.assertTrue(full_selection("main").library)
        self.assertTrue(changed_selection(branch="dev", paths=("cadlib/src/a.py",), modules=()).library)
        self.assertFalse(changed_selection(branch="dev", paths=("docs/a.md",), modules=()).library)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "build.yml"
            path.write_text("schema: 1\nbranch: issue/9\nmodules: []\nlibrary: true\ntasks: [test]\n")
            self.assertTrue(load_build(repo, "issue/9").library)
            path.write_text("schema: 1\nbranch: issue/9\nmodules: []\nlibrary: wrong\ntasks: [test]\n")
            with self.assertRaises(ConfigError):
                load_build(repo, "issue/9")

    def test_package_build_does_not_modify_source_or_install_package(self):
        owner = library_owner(Path.cwd())
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            def wheel(command, **kwargs):
                self.assertIn("wheel", command)
                self.assertIn("--no-deps", command)
                self.assertNotEqual(Path(command[-1]), owner.root)
                self.assertTrue((Path(command[-1]) / "pyproject.toml").is_file())
                (output / "cadlib_template-0.0.0-py3-none-any.whl").touch()
            with patch("cad_library_ci.library.subprocess.run", side_effect=wheel):
                build_wheel(owner, output)
