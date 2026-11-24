from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cad_library_ci.runner import execute, selected_dependencies


class RunnerTests(unittest.TestCase):
    def test_selected_dependencies_are_deduplicated_and_local_source_is_used(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            modules = []
            for name, deps in (("a", '["PyYAML==6.0.2"]'), ("b", '["PyYAML==6.0.2", "Pillow>=11"]'), ("unused", '["unused"]')):
                directory = root / name
                directory.mkdir()
                (directory / "pyproject.toml").write_text("[project]\ndependencies = " + deps)
                modules.append(SimpleNamespace(root=directory))
            selected = tuple(modules[:2])
            self.assertEqual(selected_dependencies(selected), ("PyYAML==6.0.2", "Pillow>=11"))
            with patch("cad_library_ci.runner.subprocess.run") as run:
                execute(selected)
                self.assertEqual(run.call_count, 3)
                self.assertEqual(run.call_args_list[0].args[0][-2:], ["PyYAML==6.0.2", "Pillow>=11"])
                self.assertTrue(run.call_args_list[1].kwargs["env"]["PYTHONPATH"].startswith(str(root / "a" / "src")))
