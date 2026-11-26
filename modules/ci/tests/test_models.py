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


EXPECTED_IDS = {
    "anchor-topology-mutation",
    "asymmetric-chamfer",
    "appearance-color",
    "anchored-holes",
    "as-built-attach",
    "assembly-decorator",
    "assembly-owned-anchor",
    "attach-angle",
    "attached-through-all",
    "bracket",
    "circle-negative-extrude",
    "circular-feature-pattern",
    "cylinder-subtract",
    "components",
    "configuration-installed-state",
    "configuration-position",
    "configuration-symbolic-math",
    "configuration-table",
    "cone-boolean",
    "corner-anchor",
    "eight-corner-brackets",
    "eight-flightcase-corners",
    "exploded-views",
    "four-corner-l",
    "group-hierarchy",
    "hole-family",
    "native-revolve",
    "multi-profile-extrude",
    "parameter-scope",
    "parametric-anchor",
    "parametric-attach",
    "parametric-move",
    "parametric-offset",
    "parametric-placement-pair",
    "parent-derived-child-size",
    "primitive-csg",
    "rectangular-pattern",
    "sample-plate-drawing",
    "repeated-parent-attachments",
    "revolute-joint",
    "rotated-copy-placement",
    "rotated-sketch-cutter",
    "round-top-sketch",
    "rounded-rectangle-sketch",
    "selective-profile-extrude",
    "sheet-contour-flange",
    "sheet-contour-flange-recess",
    "sheet-edge-flange",
    "sheet-fold",
    "shifted-axis-revolve",
    "sheet-hem",
    "sheet-path-flange",
    "sheet-perforate",
    "simple-box",
    "sketch-pattern-mirror",
    "slot-family",
    "top-sketch-after-chamfer",
    "topology-face-boundary-box",
    "topology-face-boundary-xz",
    "xz-anchor",
}


SCPF_ONLY_IDS = {
    "appearance-color",
    "asymmetric-chamfer",
    "attached-through-all",
    "configuration-installed-state",
    "configuration-position",
    "configuration-symbolic-math",
    "configuration-table",
    "cone-boolean",
    "exploded-views",
    "native-revolve",
    "revolute-joint",
    "rotated-sketch-cutter",
    "sheet-contour-flange",
    "sheet-contour-flange-recess",
    "sheet-edge-flange",
    "shifted-axis-revolve",
    "sheet-hem",
    "sheet-path-flange",
    "sheet-perforate",
    "sample-plate-drawing",
}

MITCAD_IDS = {
    "circle-negative-extrude",
    "cylinder-subtract",
    "multi-profile-extrude",
    "primitive-csg",
    "simple-box",
    "topology-face-boundary-box",
    "topology-face-boundary-xz",
}

MITCAD_FOCUSED_IDS = {
    "cylinder-subtract",
    "multi-profile-extrude",
    "topology-face-boundary-box",
    "topology-face-boundary-xz",
}

MITCAD_FILTERED_GEOMETRY_IDS = {
    "multi-profile-extrude",
    "topology-face-boundary-xz",
}

MITCAD_PREVIEW_IDS = {
    "circle-negative-extrude",
    "cylinder-subtract",
    "simple-box",
    "topology-face-boundary-box",
}

STANDARD_MULTI_ENGINE_IDS = (
    EXPECTED_IDS - SCPF_ONLY_IDS - MITCAD_FOCUSED_IDS
)


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

    def test_complete_migrated_owner_graph_preserves_real_implementation_sets(self):
        self.assertEqual(len(self.models), 60)
        self.assertEqual({model.id for model in self.models}, EXPECTED_IDS)
        by_id = {model.id: model for model in self.models}

        for model_id in (
            "simple-box",
            "anchored-holes",
            "corner-anchor",
            "components",
            "sample-plate-drawing",
            "configuration-installed-state",
            "configuration-position",
            "configuration-symbolic-math",
            "configuration-table",
            "shifted-axis-revolve",
        ):
            self.assertEqual(
                by_id[model_id].purposes,
                ("example", "verification"),
            )
        for model_id in set(EXPECTED_IDS) - {
            "simple-box",
            "anchored-holes",
            "corner-anchor",
            "components",
            "sample-plate-drawing",
            "configuration-installed-state",
            "configuration-position",
            "configuration-symbolic-math",
            "configuration-table",
            "shifted-axis-revolve",
        }:
            self.assertEqual(
                by_id[model_id].purposes,
                ("verification",),
            )

        for model_id in STANDARD_MULTI_ENGINE_IDS:
            model = by_id[model_id]
            expected_implementations = [
                "scpf", "cadquery", "build123d", "pythonscad", "pybosl2",
            ]
            if model_id in MITCAD_IDS:
                expected_implementations.insert(1, "scpf-mitcad")
            self.assertEqual(
                [impl.id for impl in model.implementations],
                expected_implementations,
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

        for model_id in MITCAD_FOCUSED_IDS:
            model = by_id[model_id]
            self.assertEqual(
                [impl.id for impl in model.implementations],
                ["scpf", "scpf-mitcad"],
            )
            self.assertEqual(
                [stage.id for stage in model.verifications],
                ["native", "geometry"],
            )
            self.assertEqual(
                [stage.runtime for stage in model.verifications],
                ["solidcraft", "reference"],
            )
            self.assertEqual(
                model.verifications[0].implementations,
                ("scpf",),
            )
            self.assertEqual(
                model.verifications[1].implementations,
                (
                    ("scpf", "scpf-mitcad")
                    if model_id in MITCAD_FILTERED_GEOMETRY_IDS
                    else None
                ),
            )

        for model_id in SCPF_ONLY_IDS:
            model = by_id[model_id]
            self.assertEqual(
                [impl.id for impl in model.implementations],
                ["scpf"],
            )
            if model_id == "sample-plate-drawing":
                self.assertEqual(
                    [stage.id for stage in model.verifications],
                    ["native", "drawing-sheet", "compact-drawing-sheet"],
                )
                self.assertEqual(
                    [stage.runtime for stage in model.verifications],
                    ["solidcraft", "reference", "reference"],
                )
            elif model_id == "sheet-perforate":
                self.assertEqual(
                    [stage.id for stage in model.verifications],
                    ["native", "manufacturing-visual"],
                )
                self.assertEqual(
                    [stage.runtime for stage in model.verifications],
                    ["solidcraft", "solidcraft"],
                )
            elif model_id == "multi-profile-extrude":
                self.assertEqual(
                    [stage.id for stage in model.verifications],
                    ["native", "geometry", "visual"],
                )
                self.assertEqual(
                    [stage.runtime for stage in model.verifications],
                    ["solidcraft", "reference", "solidcraft"],
                )
            elif model_id == "asymmetric-chamfer":
                self.assertEqual(
                    [stage.id for stage in model.verifications],
                    ["native", "geometry", "visual"],
                )
                self.assertEqual(
                    [stage.runtime for stage in model.verifications],
                    ["solidcraft", "reference", "solidcraft"],
                )
            else:
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
            {m.id for m in select_models(
                self.models,
                paths=(),
                selected_modules=("builder-scpf",),
            )},
            EXPECTED_IDS,
        )
        self.assertEqual(
            {m.id for m in select_models(
                self.models,
                paths=("cadlib/src/scpf/core.py",),
                library=True,
            )},
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

        self.assertEqual(invoked.call_count, 3)
        self.assertEqual(
            [manifest["runtime"] for manifest in manifests],
            ["mitcad", "solidcraft", "reference"],
        )

        mitcad = manifests[0]
        self.assertEqual(
            {
                (row["owner"], row["implementation"])
                for row in mitcad["build_items"]
            },
            {(model_id, "scpf-mitcad") for model_id in MITCAD_IDS},
        )
        self.assertEqual(mitcad["verify_items"], [])
        self.assertEqual(mitcad["preview_items"], [])

        solidcraft = manifests[1]
        self.assertEqual(
            [row["implementation"] for row in solidcraft["build_items"]],
            ["scpf"] * len(EXPECTED_IDS),
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
                    (
                        [("scpf", "native"), ("scpf", "manufacturing-visual")]
                        if model.id == "sheet-perforate"
                        else (
                            [("scpf", "native"), ("scpf", "visual")]
                            if model.id in {
                                "multi-profile-extrude",
                                "asymmetric-chamfer",
                            }
                            else [("scpf", "native")]
                        )
                    )
                    if model.id in SCPF_ONLY_IDS
                    or model.id in MITCAD_FOCUSED_IDS
                    else [("scpf", "native"), ("scpf", "visual")]
                )
            ],
        )

        reference = manifests[2]
        multi_engine = len(STANDARD_MULTI_ENGINE_IDS)
        self.assertEqual(len(reference["build_items"]), multi_engine * 4)
        expected_reference_verify_count = sum(
            len(stage.implementations)
            if stage.implementations is not None
            else len(model.implementations)
            for model in self.models
            for stage in model.verifications
            if stage.runtime == "reference"
        )
        self.assertEqual(
            len(reference["verify_items"]),
            expected_reference_verify_count,
        )
        self.assertEqual(
            len(reference["preview_items"]),
            multi_engine * 4 + len(MITCAD_PREVIEW_IDS),
        )
        self.assertEqual(
            {row["owner"] for row in reference["verify_items"]},
            (set(EXPECTED_IDS) - set(SCPF_ONLY_IDS))
            | {"sample-plate-drawing", "multi-profile-extrude", "asymmetric-chamfer"},
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
                ("scpf-mitcad", "geometry"),
                ("scpf", "drawing-sheet"),
                ("scpf", "compact-drawing-sheet"),
            },
        )


if __name__ == "__main__":
    unittest.main()
