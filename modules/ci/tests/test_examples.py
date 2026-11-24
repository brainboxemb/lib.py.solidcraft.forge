from pathlib import Path
import unittest
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.examples import discover_examples, select_examples
from cad_library_ci.batch import run_batches
from unittest.mock import patch
from types import SimpleNamespace
import tempfile
import json


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path.cwd()
        self.project = load_project(self.repo)
        self.modules = discover_modules(self.repo, self.project)
        self.examples = discover_examples(self.repo, self.modules)

    def test_discovery_and_dependency_selection(self):
        self.assertEqual([x.id for x in self.examples], [
            "simple-box", "simple-box-build123d", "simple-box-pybosl2",
            "simple-box-pythonscad", "simple-box-solidcraft",
        ])
        self.assertEqual(len(select_examples(self.examples, explicit=["simple-box"])), 1)
        self.assertEqual(len(select_examples(self.examples, paths=("docs/plan.md",), selected_modules=("verification",))), 5)
        self.assertEqual(len(select_examples(self.examples, paths=("examples/simple-box/cadquery/model.py",))), 1)
        self.assertEqual(select_examples(self.examples, paths=("docs/plan.md",)), ())
        self.assertEqual([x.id for x in select_examples(self.examples, paths=(), selected_modules=("builder-build123d",))], ["simple-box-build123d"])
        self.assertEqual([x.id for x in select_examples(self.examples, paths=(), selected_modules=("builder-pythonscad",))], ["simple-box-pybosl2", "simple-box-pythonscad"])

    def test_one_docker_invocation_per_runtime_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifests = []
            def run(command, **kwargs):
                path = next(x.split(":/manifest.json:ro")[0] for x in command if x.endswith(":/manifest.json:ro"))
                manifests.append(json.loads(Path(path).read_text()))
                return SimpleNamespace(returncode=0)
            with patch("cad_library_ci.batch.subprocess.run", side_effect=run) as invoked:
                run_batches(self.repo, self.project, self.modules, self.examples, Path(tmp))
            self.assertEqual(invoked.call_count, 2)
            self.assertEqual([m["runtime"] for m in manifests], ["solidcraft", "reference"])
            reference = manifests[1]
            self.assertEqual(len(reference["build_examples"]), 4)
            self.assertEqual(len(reference["verify_examples"]), 5)
            build123d = next(x for x in reference["build_examples"] if x["id"] == "simple-box-build123d")
            self.assertEqual(build123d["engine_python"], "/opt/build123d/bin/python")
