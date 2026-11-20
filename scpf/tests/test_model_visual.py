"""Tests for the Forge-owned SolidCraft visual adapter boundary."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "model_visual.py"
POLICY = ROOT / "examples" / "simple-box" / "verification" / "visual.json"
STAGED_MODELS = (
    "anchor-topology-mutation",
    "attach-angle",
    "four-corner-l",
    "xz-anchor",
)


def load_visual_module():
    """Load scripts/model_visual.py without making scripts a package."""

    spec = importlib.util.spec_from_file_location("model_visual", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModelVisualTests(unittest.TestCase):
    def setUp(self):
        self.visual = load_visual_module()
        self.measurements = {
            "bodies": [
                {
                    "bbox": {
                        "min": [-20.0, -15.0, 0.0],
                        "max": [20.0, 15.0, 10.0],
                    }
                }
            ]
        }

    def test_front_camera_matches_historical_simple_box_contract(self):
        camera = self.visual.solidcraft_camera(
            self.measurements,
            "front",
        )

        self.assertEqual(camera["target"], [0.0, 0.0, 5.0])
        self.assertEqual(camera["yaw"], 0.0)
        self.assertEqual(camera["pitch"], 0.0)
        self.assertEqual(camera["roll"], 0.0)
        self.assertEqual(camera["fov"], 0.0)
        self.assertAlmostEqual(camera["distance"], 66.0)

        generic = self.visual.verification_camera_values(camera)
        self.assertEqual(generic["target"], (0.0, 0.0, 5.0))
        self.assertAlmostEqual(generic["yaw_deg"], 0.0)
        self.assertAlmostEqual(generic["pitch_deg"], 0.0)
        self.assertAlmostEqual(generic["distance"], 26.4)

    def test_top_camera_maps_to_library_pitch_convention(self):
        camera = self.visual.solidcraft_camera(
            self.measurements,
            "top",
        )
        generic = self.visual.verification_camera_values(camera)

        self.assertAlmostEqual(camera["pitch"], math.pi / 2.0)
        self.assertAlmostEqual(generic["yaw_deg"], 0.0)
        self.assertAlmostEqual(generic["pitch_deg"], -90.0)
        self.assertAlmostEqual(generic["distance"], 26.4)

    def test_simple_box_policy_owns_three_approved_views_and_box(self):
        policy = self.visual.load_visual_policy(POLICY)

        self.assertEqual(tuple(policy["views"]), ("front", "right", "iso"))
        self.assertEqual(policy["render"], {"width": 720, "height": 540})
        self.assertEqual(
            policy["regression"],
            {
                "width": 96,
                "height": 72,
                "changed_pixel_threshold": 12,
                "max_mean_difference": 6,
                "max_changed_fraction": 0.08,
            },
        )
        self.assertEqual(
            policy["baseline_provenance"]["approval"],
            "approved",
        )
        self.assertEqual(
            policy["expected_boxes"],
            [
                {
                    "label": "SimpleBox",
                    "minimum": [-20, -15, 0],
                    "maximum": [20, 15, 10],
                }
            ],
        )

        for view in policy["views"].values():
            baseline = POLICY.parent / view["baseline"]
            self.assertTrue(baseline.is_file(), baseline)
            self.assertGreater(baseline.stat().st_size, 0)

    def test_staged_models_use_approved_encoded_baselines(self):
        expected_box_counts = {
            "anchor-topology-mutation": 2,
            "attach-angle": 2,
            "four-corner-l": 9,
            "xz-anchor": 3,
        }
        for slug in STAGED_MODELS:
            with self.subTest(slug=slug):
                policy_path = (
                    ROOT / "examples" / slug / "verification" / "visual.json"
                )
                policy = self.visual.load_visual_policy(policy_path)
                self.assertEqual(
                    tuple(policy["views"]),
                    ("front", "right", "iso"),
                )
                self.assertEqual(
                    len(policy["expected_boxes"]),
                    expected_box_counts[slug],
                )
                self.assertEqual(
                    policy["baseline_provenance"]["approval"],
                    "approved",
                )
                for view in policy["views"].values():
                    self.assertNotIn("baseline", view)
                    payload_path = policy_path.parent / view["baseline_payload"]
                    payload = json.loads(
                        payload_path.read_text(encoding="utf-8")
                    )
                    self.assertEqual(payload["approval"], "approved")
                    self.assertEqual(payload["encoding"], "zlib")
                    self.assertEqual(payload["width"], 96)
                    self.assertEqual(payload["height"], 72)
                    self.assertTrue(payload["data"])

                ci_text = (
                    ROOT / "examples" / slug / "ci.yml"
                ).read_text(encoding="utf-8")
                self.assertIn("process: true", ci_text)

    def test_presentation_preview_reuses_current_iso_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            model = output / "native" / "model.sc"
            model.parent.mkdir(parents=True)
            model.write_text("model", encoding="utf-8")
            measurements = output / "baseline" / "measurements.json"
            measurements.parent.mkdir(parents=True)
            measurements.write_text(
                json.dumps(self.measurements),
                encoding="utf-8",
            )
            iso = output / "visual" / "iso" / "actual.png"
            iso.parent.mkdir(parents=True)
            iso.write_bytes(b"current-visual")

            with mock.patch.object(self.visual, "_snapshot") as snapshot:
                metadata = self.visual.write_presentation_preview(
                    model,
                    measurements,
                    output,
                )

            snapshot.assert_not_called()
            preview = output / "presentation" / "preview-iso.png"
            self.assertEqual(preview.read_bytes(), b"current-visual")
            self.assertEqual(metadata["renderer"], "reused-visual")
            self.assertEqual(metadata["source"], "visual/iso/actual.png")
            self.assertEqual(metadata["width"], 720)
            self.assertEqual(metadata["height"], 540)
            stored = json.loads(
                (output / "presentation" / "preview.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(stored, metadata)

    def test_presentation_preview_snapshots_when_visual_iso_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            model = output / "native" / "model.sc"
            model.parent.mkdir(parents=True)
            model.write_text("model", encoding="utf-8")
            measurements = output / "baseline" / "measurements.json"
            measurements.parent.mkdir(parents=True)
            measurements.write_text(
                json.dumps(self.measurements),
                encoding="utf-8",
            )

            def fake_snapshot(
                model_path,
                output_path,
                camera,
                *,
                width,
                height,
            ):
                self.assertEqual(Path(model_path), model.resolve())
                self.assertEqual(width, 720)
                self.assertEqual(height, 540)
                self.assertAlmostEqual(camera["yaw"], -math.pi / 4.0)
                self.assertAlmostEqual(camera["pitch"], math.radians(32.0))
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_bytes(b"snapshot")

            with mock.patch.object(
                self.visual,
                "_snapshot",
                side_effect=fake_snapshot,
            ) as snapshot:
                metadata = self.visual.write_presentation_preview(
                    model,
                    measurements,
                    output,
                )

            snapshot.assert_called_once()
            self.assertEqual(
                (output / "presentation" / "preview-iso.png").read_bytes(),
                b"snapshot",
            )
            self.assertEqual(metadata["renderer"], "solidcraft-snapshot")
            self.assertEqual(metadata["source"], "native/model.sc")
            self.assertEqual(metadata["camera"]["target"], [0.0, 0.0, 5.0])

    def test_adapter_delegates_generic_visual_mechanics_to_library(self):
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("verify_visual_view", text)
        self.assertIn("compose_semantic_result", text)
        self.assertIn("decode_baseline", text)
        self.assertIn('"solidcraft-cli"', text)
        self.assertIn('"snapshot"', text)

        for forbidden in (
            "from PIL",
            "import PIL",
            "compare_images",
            "write_diff_image",
            "project_points",
            "make_goal_image",
            "make_overlay_image",
            "ImageDraw",
            "b64decode",
            "import zlib",
            "zlib.decompress",
        ):
            self.assertNotIn(forbidden, text)

    def test_policy_is_data_only_json(self):
        value = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(value["schema"], 1)


if __name__ == "__main__":
    unittest.main()
