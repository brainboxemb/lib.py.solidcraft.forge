from pathlib import Path
import unittest
import yaml

from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules


class LibraryLayoutTests(unittest.TestCase):
    def test_library_and_verification_starters(self):
        for root, kind in ((Path("cadlib"), "library"), (Path("modules/verification"), "python")):
            with self.subTest(root=root):
                self.assertEqual(yaml.safe_load((root / "ci.yml").read_text())["kind"], kind)
                self.assertTrue((root / "pyproject.toml").is_file())
                self.assertTrue(any((root / "src").rglob("*.py")))
                self.assertTrue(any((root / "tests").glob("test_*.py")))
        self.assertTrue(Path("examples/README.md").is_file())
        self.assertFalse(Path("verification").exists())

    def test_verification_is_discovered_as_a_normal_module(self):
        repo = Path.cwd()
        modules = discover_modules(repo, load_project(repo))
        self.assertIn("verification", {item.id for item in modules})
