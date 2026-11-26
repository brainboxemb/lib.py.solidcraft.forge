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

    def test_all_migrated_visual_policies_are_approved_and_supported(self):
        repo = Path(__file__).resolve().parents[3]
        paths = sorted((repo / "models").glob("*/verification/visual.json"))
        self.assertEqual(len(paths), 38)
        feature_types = set()
        for path in paths:
            policy = solidcraft_visual.load_visual_policy(path)
            self.assertEqual(policy["baseline_provenance"]["approval"], "approved")
            self.assertEqual(tuple(policy["views"]), ("front", "right", "iso"))
            self.assertTrue(policy["expected_views"])
            self.assertTrue(policy["expected_boxes"])
            feature_types.update(
                feature["type"] for feature in policy.get("expected_features", [])
            )
        self.assertEqual(
            feature_types,
            {"through_hole", "through_slot", "through_path_slot"},
        )

    def test_standard_report_projects_view_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native")
            policy = root / "visual.json"
            policy.write_text("{}")
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
