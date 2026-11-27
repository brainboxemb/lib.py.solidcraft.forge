"""SolidCraft visual adapter contract tests."""

from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from cad_verification.adapters import solidcraft_visual



class SolidCraftVisualAdapterTests(unittest.TestCase):
    def setUp(self):
        self.measurements = {
            "bodies": [
                {"bbox": {"min": [-20.0, -15.0, 0.0], "max": [20.0, 15.0, 10.0]}}
            ]
        }

    def test_historical_camera_contract(self):
        front = solidcraft_visual.solidcraft_camera(self.measurements, "front")
        self.assertEqual(front["target"], [0.0, 0.0, 5.0])
        self.assertEqual(front["yaw"], 0.0)
        self.assertEqual(front["pitch"], 0.0)
        self.assertAlmostEqual(front["distance"], 66.0)

        top = solidcraft_visual.solidcraft_camera(self.measurements, "top")
        generic = solidcraft_visual.verification_camera_values(top)
        self.assertAlmostEqual(top["pitch"], math.pi / 2.0)
        self.assertAlmostEqual(generic["pitch_deg"], -90.0)

    def test_policy_requires_approved_per_view_baselines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "baseline.png").write_bytes(b"x")
            path = root / "visual.json"
            path.write_text(json.dumps({
                "schema": 1,
                "views": {"front": {"baseline": "baseline.png"}},
                "render": {"width": 720, "height": 540},
                "regression": {
                    "width": 96,
                    "height": 72,
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 6,
                    "max_changed_fraction": 0.08,
                },
                "baseline_provenance": {"approval": "approved"},
                "expected_boxes": [{
                    "label": "box",
                    "minimum": [-20, -15, 0],
                    "maximum": [20, 15, 10],
                }],
            }))
            policy = solidcraft_visual.load_visual_policy(path)
            self.assertEqual(tuple(policy["views"]), ("front",))
            self.assertEqual(tuple(policy["expected_views"]), ("front",))

    def test_policy_allows_baseline_only_native_visual_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "baseline.png").write_bytes(b"x")
            (root / "service.json").write_text('{"commands": []}')
            path = root / "visual.json"
            path.write_text(json.dumps({
                "schema": 1,
                "state": {"id": "service", "command": "service.json"},
                "views": {"iso": {"baseline": "baseline.png"}},
                "expected_views": [],
                "render": {"width": 720, "height": 540},
                "regression": {
                    "width": 96,
                    "height": 72,
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 6,
                    "max_changed_fraction": 0.08,
                },
                "baseline_provenance": {"approval": "approved"},
            }))
            policy = solidcraft_visual.load_visual_policy(path)
            self.assertEqual(policy["state"]["id"], "service")
            self.assertEqual(policy["expected_views"], [])
            self.assertEqual(policy.get("expected_boxes", []), [])

    def test_policy_accepts_rgb_regression_mode_and_rejects_unknown_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "baseline.png").write_bytes(b"x")
            path = root / "visual.json"
            policy = {
                "schema": 1,
                "views": {"iso": {"baseline": "baseline.png"}},
                "expected_views": [],
                "render": {"width": 720, "height": 540},
                "regression": {
                    "mode": "rgb",
                    "width": 96,
                    "height": 72,
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 6,
                    "max_changed_fraction": 0.08,
                },
                "baseline_provenance": {"approval": "approved"},
            }
            path.write_text(json.dumps(policy))
            loaded = solidcraft_visual.load_visual_policy(path)
            self.assertEqual(loaded["regression"]["mode"], "rgb")

            policy["regression"]["mode"] = "lab"
            path.write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError, "grayscale or rgb"):
                solidcraft_visual.load_visual_policy(path)

    def test_standard_report_materializes_native_state_before_visual_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native")
            command = root / "service.json"
            command.write_text('{"commands": []}')
            baseline = root / "baseline.png"
            baseline.write_bytes(b"baseline")
            policy = root / "visual.json"
            policy.write_text(json.dumps({
                "schema": 1,
                "state": {"id": "service", "command": "service.json"},
                "views": {"iso": {"baseline": "baseline.png"}},
                "expected_views": [],
                "render": {"width": 720, "height": 540},
                "regression": {
                    "width": 96,
                    "height": 72,
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 6,
                    "max_changed_fraction": 0.08,
                },
                "baseline_provenance": {"approval": "approved"},
            }))
            output = root / "out"

            rendered_models = []

            def fake_mutate(source, command_path, destination):
                self.assertEqual(Path(source), model)
                self.assertEqual(Path(command_path), command)
                destination = Path(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("mutated")
                return destination

            def fake_eval(source, destination):
                rendered_models.append(Path(source))
                Path(destination).write_text(json.dumps(self.measurements))
                return self.measurements

            def fake_visual(source, _measurements, _policy, destination):
                rendered_models.append(Path(source))
                view = Path(destination) / "visual/iso"
                view.mkdir(parents=True)
                (view / "actual.png").write_bytes(b"actual")
                (view / "diff.png").write_bytes(b"diff")
                (view / "camera.json").write_text("{}")
                report = {
                    "schema": "forge-visual-verification",
                    "schema_version": 1,
                    "status": "pass",
                    "baseline_provenance": {"approval": "approved"},
                    "state": {"id": "service", "command": "service.json"},
                    "views": [{
                        "view": "iso",
                        "status": "pass",
                        "regression_required": True,
                        "expected_shape_required": False,
                        "camera": "visual/iso/camera.json",
                        "baseline": "baseline.png",
                        "evidence": {
                            "actual_image": "visual/iso/actual.png",
                            "baseline_status": "pass",
                            "regression": {"pass": True},
                            "diff_image": "visual/iso/diff.png",
                            "goal_image": None,
                            "overlay_image": None,
                            "expected_shape_status": None,
                        },
                    }],
                }
                (Path(destination) / "visual.json").write_text(json.dumps(report))
                return report

            with mock.patch(
                "cad_verification.adapters.solidcraft.mutate_solidcraft_model",
                side_effect=fake_mutate,
            ), mock.patch(
                "cad_verification.adapters.solidcraft.evaluate_solidcraft_model",
                side_effect=fake_eval,
            ), mock.patch.object(
                solidcraft_visual,
                "run_visual_verification",
                side_effect=fake_visual,
            ):
                report = solidcraft_visual.run_solidcraft_visual_verification_file(
                    model,
                    output,
                    policy,
                    verification_id="state-visual",
                )

            state_model = output / "state/service/model.sc"
            self.assertEqual(rendered_models, [state_model, state_model])
            self.assertEqual(report["metadata"]["state"]["id"], "service")
            self.assertEqual(
                report["metadata"]["rendered_model"],
                "state/service/model.sc",
            )
            self.assertTrue(
                any(
                    artifact["path"] == "state/service/model.sc"
                    for artifact in report["checks"][0]["artifacts"]
                )
            )

    def test_all_migrated_visual_policies_are_approved_and_supported(self):
        repo = Path(__file__).resolve().parents[3]
        paths = sorted((repo / "models").glob("*/verification/visual*.json"))
        self.assertEqual(len(paths), 54)
        state_policies = {
            ("appearance-color", "visual-color.json"): (("iso",), None, "rgb"),
            ("configuration-installed-state", "visual-large-installed.json"): (("top",), "large-installed", "grayscale"),
            ("configuration-installed-state", "visual-large-free.json"): (("top",), "large-free", "grayscale"),
            ("configuration-position", "visual-front.json"): (("right",), None, "grayscale"),
            ("configuration-position", "visual-service.json"): (("right",), "service", "grayscale"),
            ("revolute-joint", "visual-60.json"): (("iso",), None, "grayscale"),
            ("revolute-joint", "visual-120.json"): (("iso",), "drive-120", "grayscale"),
            ("shifted-axis-revolve", "visual-cut.json"): (("front",), None, "grayscale"),
            ("shifted-axis-revolve", "visual-suppressed.json"): (("front",), "suppressed", "grayscale"),
        }
        seen_state_policies = set()
        feature_types = set()
        for path in paths:
            policy = solidcraft_visual.load_visual_policy(path)
            self.assertEqual(policy["baseline_provenance"]["approval"], "approved")
            owner = path.parents[1].name
            key = (owner, path.name)
            if path.name == "visual.json":
                self.assertEqual(tuple(policy["views"]), ("front", "right", "iso"))
                self.assertTrue(policy["expected_views"])
                self.assertTrue(policy["expected_boxes"])
            else:
                self.assertIn(key, state_policies)
                views, state_id, mode = state_policies[key]
                seen_state_policies.add(key)
                self.assertEqual(tuple(policy["views"]), views)
                self.assertEqual(policy["expected_views"], [])
                self.assertEqual(policy.get("expected_boxes", []), [])
                self.assertEqual(policy["regression"]["mode"], mode)
                provenance = policy["baseline_provenance"]
                self.assertEqual(
                    provenance["source_commit"],
                    "83e2274e4fa530309352f81653d42c41088c3267",
                )
                self.assertEqual(provenance["workflow_run"], 45916016779)
                self.assertEqual(provenance["solidcraft_version"], "0.49.0")
                self.assertEqual(
                    provenance["runtime"],
                    "ghcr.io/brainboxemb/cad-solidcraft:v0.3.6",
                )
                self.assertNotIn("capture_seed", provenance)
                self.assertNotIn("not_for_merge", provenance)
                state = policy.get("state")
                if state_id is None:
                    self.assertIsNone(state)
                else:
                    self.assertIsNotNone(state)
                    self.assertEqual(state["id"], state_id)
            feature_types.update(
                feature["type"] for feature in policy.get("expected_features", [])
            )
        self.assertEqual(seen_state_policies, set(state_policies))
        self.assertEqual(
            feature_types,
            {"through_hole", "through_slot", "through_path_slot"},
        )

    def test_standard_report_projects_view_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native")
            baseline = root / "baseline.png"
            baseline.write_bytes(b"baseline")
            policy = root / "visual.json"
            policy.write_text(json.dumps({
                "schema": 1,
                "views": {"front": {"baseline": "baseline.png"}},
                "expected_views": [],
                "render": {"width": 720, "height": 540},
                "regression": {
                    "width": 96,
                    "height": 72,
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 6,
                    "max_changed_fraction": 0.08,
                },
                "baseline_provenance": {"approval": "approved"},
            }))
            output = root / "out"

            def fake_eval(_model, destination):
                Path(destination).write_text(json.dumps(self.measurements))
                return self.measurements

            def fake_visual(_model, _measurements, _policy, destination):
                view = Path(destination) / "visual/front"
                view.mkdir(parents=True)
                for name in ("actual.png", "goal.png", "overlay.png", "diff.png"):
                    (view / name).write_bytes(name.encode())
                (view / "camera.json").write_text("{}")
                report = {
                    "schema": "forge-visual-verification",
                    "schema_version": 1,
                    "status": "pass",
                    "baseline_provenance": {"approval": "approved"},
                    "views": [{
                        "view": "front",
                        "status": "pass",
                        "regression_required": True,
                        "expected_shape_required": True,
                        "camera": "visual/front/camera.json",
                        "baseline": "baselines/front.png",
                        "evidence": {
                            "actual_image": "visual/front/actual.png",
                            "baseline_status": "pass",
                            "regression": {"pass": True},
                            "diff_image": "visual/front/diff.png",
                            "goal_image": "visual/front/goal.png",
                            "overlay_image": "visual/front/overlay.png",
                            "expected_shape_status": "pass",
                        },
                    }],
                }
                (Path(destination) / "visual.json").write_text(json.dumps(report))
                return report

            with mock.patch(
                "cad_verification.adapters.solidcraft.evaluate_solidcraft_model",
                side_effect=fake_eval,
            ), mock.patch.object(
                solidcraft_visual,
                "run_visual_verification",
                side_effect=fake_visual,
            ):
                report = solidcraft_visual.run_solidcraft_visual_verification_file(
                    model,
                    output,
                    policy,
                    verification_id="box-scpf-visual",
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["checks"][0]["id"], "front")
            self.assertEqual(len(report["checks"][0]["artifacts"]), 5)
            stored = json.loads((output / "verification.json").read_text())
            self.assertEqual(stored, report)


if __name__ == "__main__":
    unittest.main()
