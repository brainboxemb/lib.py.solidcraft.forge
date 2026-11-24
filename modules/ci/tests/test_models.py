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


EXPECTED_IDS = [
    "anchored-holes",
    "assembly-decorator",
    "attached-through-all",
    "bracket",
    "circle-negative-extrude",
    "circular-feature-pattern",
    "cone-boolean",
    "corner-anchor",
    "hole-family",
    "native-revolve",
    "parametric-attach",
    "primitive-csg",
    "rectangular-pattern",
    "rotated-sketch-cutter",
    "round-top-sketch",
    "rounded-rectangle-sketch",
    "sheet-fold",
    "simple-box",
    "slot-family",
    "top-sketch-after-chamfer",
]


SCPF_ONLY_IDS = [
    "attached-through-all",
    "cone-boolean",
    "native-revolve",
    "rotated-sketch-cutter",
]


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

    def test_twenty_historical_owners_preserve_real_implementation_sets(self):
        self.assertEqual(
            [model.id for model in self.models],
            EXPECTED_IDS,
        )
        by_id = {model.id: model for model in self.models}

        for model_id in (
            "simple-box",
            "anchored-holes",
            "corner-anchor",
        ):
            self.assertEqual(
                by_id[model_id].purposes,
                ("example", "verification"),
            )
        for model_id in set(EXPECTED_IDS) - {
            "simple-box",
            "anchored-holes",
            "corner-anchor",
        }:
            self.assertEqual(
                by_id[model_id].purposes,
                ("verification",),
            )

        for model_id in set(EXPECTED_IDS) - set(SCPF_ONLY_IDS):
            model = by_id[model_id]
            self.assertEqual(
                [impl.id for impl in model.implementations],
                ["scpf", "cadquery", "build123d", "pythonscad", "pybosl2"],
            )
            expected_stages = ["native", "geometry", "visual"]
            expected_runtimes = ["solidcraft", "reference", "solidcraft"]
            self.assertEqual(
                [stage.id for stage in model.verifications],
                expected_stages,
            )
            self.assertEqual(
                [stage.runtime for stage in model.verifications],
                expected_runtimes,
            )
            self.assertEqual(
                model.verifications[0].implementations,
                ("scpf",),
            )
            self.assertEqual(
                model.verifications[2].implementations,
                ("scpf",),
            )

        for model_id in SCPF_ONLY_IDS:
            model = by_id[model_id]
            self.assertEqual(
                [impl.id for impl in model.implementations],
                ["scpf"],
            )
            self.assertEqual(
                [stage.id for stage in model.verifications],
                ["native"],
            )
            self.assertEqual(
                [stage.runtime for stage in model.verifications],
                ["solidcraft"],
            )

        for model in self.models:
            self.assertEqual(model.primary, "scpf")
            self.assertTrue(model.needs_cadlib)

    def test_owner_selection_uses_paths_builder_and_library_dependencies(self):
        self.assertEqual(
            [m.id for m in select_models(self.models, explicit=["simple-box"])],
            ["simple-box"],
        )
        self.assertEqual(
            [m.id for m in select_models(
                self.models,
                paths=("models/rotated-sketch-cutter/scpf/model.py",),
            )],
            ["rotated-sketch-cutter"],
        )
        self.assertEqual(
            [m.id for m in select_models(
                self.models,
                paths=(),
                selected_modules=("builder-scpf",),
            )],
            EXPECTED_IDS,
        )
        self.assertEqual(
            [m.id for m in select_models(
                self.models,
                paths=("cadlib/src/scpf/core.py",),
                library=True,
            )],
            EXPECTED_IDS,
        )

    def test_one_docker_invocation_per_required_runtime_role(self):
        manifests = []

        def run(command, **kwargs):
            path = next(
                item.split(":/manifest.json:ro")[0]
                for item in command
                if item.endswith(":/manifest.json:ro")
            )
            manifests.append(json.loads(Path(path).read_text()))
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

        solidcraft = manifests[0]
        self.assertEqual(
            [row["implementation"] for row in solidcraft["build_items"]],
            ["scpf"] * 20,
        )
        self.assertEqual(
            [
                (row["implementation"], row["stage_id"])
                for row in solidcraft["verify_items"]
            ],
            [
                pair
                for model in self.models
                for pair in (
                    [("scpf", "native")]
                    if model.id in SCPF_ONLY_IDS
                    else [("scpf", "native"), ("scpf", "visual")]
                )
            ],
        )

        reference = manifests[1]
        self.assertEqual(len(reference["build_items"]), 64)
        self.assertEqual(len(reference["verify_items"]), 80)
        self.assertEqual(len(reference["preview_items"]), 64)
        self.assertEqual(
            {row["owner"] for row in reference["verify_items"]},
            set(EXPECTED_IDS) - set(SCPF_ONLY_IDS),
        )
        self.assertEqual(
            {
                (row["implementation"], row["stage_id"])
                for row in reference["verify_items"]
            },
            {
                ("scpf", "geometry"),
                ("cadquery", "geometry"),
                ("build123d", "geometry"),
                ("pythonscad", "geometry"),
                ("pybosl2", "geometry"),
            },
        )


if __name__ == "__main__":
    unittest.main()
