from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cad_library_ci.runner import (
    execute,
    execute_model_tests,
    selected_dependencies,
)


class RunnerTests(unittest.TestCase):
    def test_selected_dependencies_are_deduplicated_and_local_source_is_used(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            modules = []
            for name, deps in (
                ("a", '["PyYAML==6.0.2"]'),
                ("b", '["PyYAML==6.0.2", "Pillow>=11"]'),
                ("unused", '["unused"]'),
            ):
                directory = root / name
                directory.mkdir()
                (directory / "pyproject.toml").write_text(
                    "[project]\ndependencies = " + deps
                )
                modules.append(SimpleNamespace(root=directory))
            selected = tuple(modules[:2])
            self.assertEqual(
                selected_dependencies(selected),
                ("PyYAML==6.0.2", "Pillow>=11"),
            )
            with patch("cad_library_ci.runner.subprocess.run") as run:
                execute(selected)
                self.assertEqual(run.call_count, 3)
                self.assertEqual(
                    run.call_args_list[0].args[0][-2:],
                    ["PyYAML==6.0.2", "Pillow>=11"],
                )
                self.assertTrue(
                    run.call_args_list[1]
                    .kwargs["env"]["PYTHONPATH"]
                    .startswith(str(root / "a" / "src"))
                )

    def test_model_tests_run_only_for_selected_owners_with_tests(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            library = repo / "cadlib"
            (library / "src").mkdir(parents=True)
            (library / "pyproject.toml").write_text(
                '[project]\ndependencies = ["dependency==1"]\n'
            )

            tested = repo / "models/tested"
            skipped = repo / "models/skipped"
            (tested / "tests").mkdir(parents=True)
            skipped.mkdir(parents=True)
            (tested / "tests/test_contract.py").write_text(
                "import unittest\n"
            )
            models = (
                SimpleNamespace(root=tested),
                SimpleNamespace(root=skipped),
            )
            owner = SimpleNamespace(root=library)

            with patch("cad_library_ci.runner.subprocess.run") as run:
                execute_model_tests(
                    repo,
                    models,
                    owner,
                    dependencies_installed=False,
                )

            self.assertEqual(run.call_count, 2)
            self.assertIn("dependency==1", run.call_args_list[0].args[0])
            command = run.call_args_list[1].args[0]
            self.assertEqual(command[2:5], ["unittest", "discover", "-s"])
            self.assertEqual(Path(command[5]), tested / "tests")
            path = run.call_args_list[1].kwargs["env"]["PYTHONPATH"]
            self.assertTrue(path.startswith(str(library / "src")))
            self.assertIn(str(tested), path)

    def test_model_tests_do_not_reinstall_library_dependencies_when_library_selected(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            library = repo / "cadlib"
            (library / "src").mkdir(parents=True)
            (library / "pyproject.toml").write_text(
                '[project]\ndependencies = ["dependency==1"]\n'
            )
            model = repo / "models/tested"
            (model / "tests").mkdir(parents=True)
            owner = SimpleNamespace(root=library)

            with patch("cad_library_ci.runner.subprocess.run") as run:
                execute_model_tests(
                    repo,
                    (SimpleNamespace(root=model),),
                    owner,
                    dependencies_installed=True,
                )
            self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
