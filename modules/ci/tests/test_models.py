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
        self.models = discover_models(
            self.repo,
            self.project,
            self.modules,
        )

    def test_historical_owner_has_scpf_and_four_reference_implementations(self):
        self.assertEqual(
            [model.id for model in self.models],
            ["simple-box"],
        )
        model = self.models[0]
        self.assertEqual(
            [impl.id for impl in model.implementations],
            [
                "scpf",
                "cadquery",
                "build123d",
                "pythonscad",
                "pybosl2",
            ],
        )
        self.assertEqual(
            model.purposes,
            ("example", "verification"),
        )
        self.assertEqual(model.primary, "scpf")
        self.assertTrue(model.needs_cadlib)

    def test_owner_selection_uses_paths_builder_and_library_dependencies(self):
        self.assertEqual(
            [
                model.id
                for model in select_models(
                    self.models,
                    explicit=["simple-box"],
                )
            ],
            ["simple-box"],
        )
        self.assertEqual(
            [
                model.id
                for model in select_models(
                    self.models,
                    paths=("models/simple-box/scpf/model.py",),
                )
            ],
            ["simple-box"],
        )
        self.assertEqual(
            [
                model.id
                for model in select_models(
                    self.models,
                    paths=(),
                    selected_modules=("builder-scpf",),
                )
            ],
            ["simple-box"],
        )
        self.assertEqual(
            [
                model.id
                for model in select_models(
                    self.models,
                    paths=("cadlib/src/scpf/core.py",),
                    library=True,
                )
            ],
            ["simple-box"],
        )

    def test_one_docker_invocation_per_required_runtime_role(self):
        manifests = []

        def run(command, **kwargs):
            path = next(
                item.split(":/manifest.json:ro")[0]
                for item in command
                if item.endswith(":/manifest.json:ro")
            )
            manifests.append(
                json.loads(Path(path).read_text())
            )
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "cad_library_ci.batch.subprocess.run",
                side_effect=run,
            ) as invoked, patch(
                "cad_library_ci.batch._aggregate_model",
                return_value=True,
            ):
                run_batches(
                    self.repo,
                    self.project,
                    self.modules,
                    self.models,
                    Path(tmp),
                )

        self.assertEqual(invoked.call_count, 2)
        self.assertEqual(
            [manifest["runtime"] for manifest in manifests],
            ["solidcraft", "reference"],
        )
        self.assertEqual(
            [
                row["implementation"]
                for row in manifests[0]["build_items"]
            ],
            ["scpf"],
        )
        reference = manifests[1]
        self.assertEqual(len(reference["build_items"]), 4)
        self.assertEqual(len(reference["verify_items"]), 5)


if __name__ == "__main__":
    unittest.main()
