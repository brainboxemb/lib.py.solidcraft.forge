from pathlib import Path
import tempfile
import unittest
from cad_library_ci.config import load_build, ConfigError
from cad_library_ci.items import PythonModule, select
from cad_library_ci.selection import changed_selection

class SelectionTests(unittest.TestCase):
    def test_stale_build_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "build.yml").write_text("schema: 1\nbranch: issue/1\nmodules: [ci]\ntasks: [test]\n")
            self.assertIsNone(load_build(repo, "issue/2"))
            self.assertEqual(load_build(repo, "issue/1").modules, ("ci",))

    def test_impact(self):
        modules = (PythonModule("ci", Path("modules/ci"), "full", ("modules/ci/**",)), PythonModule("pages", Path("modules/pages"), "self", ("site/**",)))
        self.assertEqual(changed_selection(branch="dev", paths=("site/a",), modules=modules).modules, ("pages",))
        self.assertIsNone(changed_selection(branch="dev", paths=("modules/ci/a",), modules=modules).modules)
        self.assertIsNone(changed_selection(branch="dev", paths=("ci.yml",), modules=modules).modules)
        self.assertEqual(changed_selection(branch="dev", paths=("docs/a",), modules=modules).modules, ())
        with self.assertRaises(ConfigError):
            select(modules, ("missing",))
