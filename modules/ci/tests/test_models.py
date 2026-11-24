from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.batch import run_batches
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.models import discover_models, select_models


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path.cwd()
        self.project = load_project(self.repo)
        self.modules = discover_modules(self.repo, self.project)
        self.models = discover_models(self.repo, self.project, self.modules)

    def test_one_owner_has_five_engine_implementations_and_multiple_purposes(self):
        self.assertEqual([model.id for model in self.models], ["simple-box"])
        model = self.models[0]
        self.assertEqual(
            [impl.id for impl in model.implementations],
            ["cadquery", "build123d", "pythonscad", "pybosl2", "solidcraft"],
        )
        self.assertEqual(model.purposes, ("example", "verification"))
        self.assertEqual(model.primary, "cadquery")

    def test_owner_selection_uses_paths_and_builder_dependencies(self):
        self.assertEqual(
            [m.id for m in select_models(self.models, explicit=["simple-box"])],
            ["simple-box"],
        )
        self.assertEqual(
            [m.id for m in select_models(
                self.models,
                paths=("models/simple-box/cadquery/model.py",),
            )],
            ["simple-box"],
        )
        self.assertEqual(
            [m.id for m in select_models(
                self.models,
                paths=(),
                selected_modules=("builder-build123d",),
            )],
            ["simple-box"],
        )
        self.assertEqual(
            select_models(self.models, paths=("docs/plan.md",)),
            (),
        )

    def test_one_docker_invocation_per_required_runtime_role(self):
        manifests = []
        def run(command, **kwargs):
            path = next(
                x.split(":/manifest.json:ro")[0]
                for x in command
                if x.endswith(":/manifest.json:ro")
            )
            manifests.append(json.loads(Path(path).read_text()))
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("cad_library_ci.batch.subprocess.run", side_effect=run) as invoked, \
                 patch("cad_library_ci.batch._aggregate_model", return_value=True):
                run_batches(
                    self.repo,
                    self.project,
                    self.modules,
                    self.models,
                    Path(tmp),
                )
        self.assertEqual(invoked.call_count, 2)
        self.assertEqual([m["runtime"] for m in manifests], ["solidcraft", "reference"])
        self.assertEqual(
            [row["implementation"] for row in manifests[0]["build_items"]],
            ["solidcraft"],
        )
        reference = manifests[1]
        self.assertEqual(len(reference["build_items"]), 4)
        self.assertEqual(len(reference["verify_items"]), 5)
        build123d = next(
            row for row in reference["build_items"]
            if row["implementation"] == "build123d"
        )
        self.assertEqual(build123d["engine_python"], "/opt/build123d/bin/python")


if __name__ == "__main__":
    unittest.main()
