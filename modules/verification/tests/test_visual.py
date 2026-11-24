"""Requirement tests for generic visual verification primitives."""

from __future__ import annotations

from base64 import b64encode
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

import cad_verification.visual as visual_module
from cad_verification import (
    ExpectedBox,
    OrthographicCamera,
    ThroughHole,
    ThroughPathSlot,
    ThroughSlot,
    VerificationConfigError,
    VerificationFailure,
    VisualEvidenceError,
    VisualViewEvidence,
    compare_images,
    decode_baseline,
    draw_expected_geometry,
    encode_baseline,
    make_goal_image,
    make_overlay_image,
    normalize_image,
    project_points,
    verify_visual_view,
    write_diff_image,
)


class VisualVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_image(
        self,
        name: str,
        mode: str,
        size: tuple[int, int],
        value,
    ) -> Path:
        path = self.root / name
        Image.new(mode, size, value).save(path)
        return path

    def front_camera(self) -> OrthographicCamera:
        return OrthographicCamera(
            target=(0, 0, 0),
            yaw_deg=0,
            pitch_deg=0,
            distance=10,
        )

    def top_camera(self) -> OrthographicCamera:
        return OrthographicCamera(
            target=(0, 0, 0),
            yaw_deg=0,
            pitch_deg=-90,
            distance=10,
        )

    def test_r1_normalize_rgb_rgba_resize_and_errors(self):
        rgb = self.write_image("rgb.png", "RGB", (8, 6), (10, 20, 30))
        rgba = self.write_image(
            "rgba.png",
            "RGBA",
            (4, 3),
            (10, 20, 30, 100),
        )
        first = normalize_image(rgb, 5, 7)
        second = normalize_image(rgba, 5, 7)
        self.assertEqual(first.mode, "L")
        self.assertEqual(second.mode, "L")
        self.assertEqual(first.size, (5, 7))
        self.assertEqual(second.size, (5, 7))

        with self.assertRaises(VisualEvidenceError):
            normalize_image(self.root / "missing.png", 5, 7)

        invalid = self.root / "invalid.png"
        invalid.write_text("not an image", encoding="utf-8")
        with self.assertRaises(VisualEvidenceError):
            normalize_image(invalid, 5, 7)

        with self.assertRaises(VerificationConfigError):
            normalize_image(rgb, 0, 7)

    def test_r2_baseline_raw_zlib_and_png_round_trip(self):
        image = Image.new("L", (4, 3))
        image.putdata(range(12))

        for encoding in ("raw", "zlib", "png"):
            with self.subTest(encoding=encoding):
                payload = encode_baseline(image, encoding=encoding)
                restored = decode_baseline(payload)
                self.assertEqual(restored.mode, "L")
                self.assertEqual(restored.size, image.size)
                self.assertEqual(restored.tobytes(), image.tobytes())

        broken = {
            "encoding": "raw",
            "width": 4,
            "height": 3,
            "data": b64encode(b"too-short").decode("ascii"),
        }
        with self.assertRaises(VisualEvidenceError):
            decode_baseline(broken)

        corrupt = {
            "encoding": "zlib",
            "width": 4,
            "height": 3,
            "data": b64encode(b"not-zlib").decode("ascii"),
        }
        with self.assertRaises(VisualEvidenceError):
            decode_baseline(corrupt)

    def test_r3_regression_metrics_and_independent_limits(self):
        reference = Image.new("L", (10, 10), 100)
        identical = Image.new("L", (10, 10), 100)
        evidence = compare_images(
            identical,
            reference,
            changed_pixel_threshold=10,
            max_mean_difference=0,
            max_changed_fraction=0,
        )
        self.assertEqual(evidence["mean_absolute_difference"], 0.0)
        self.assertEqual(evidence["changed_pixel_fraction"], 0.0)

        small = reference.copy()
        small.putpixel((0, 0), 105)
        passed = compare_images(
            small,
            reference,
            changed_pixel_threshold=10,
            max_mean_difference=0.1,
            max_changed_fraction=0,
        )
        self.assertTrue(passed["pass"])

        mean_fail = reference.copy()
        mean_fail.putpixel((0, 0), 120)
        with self.assertRaises(VerificationFailure) as caught:
            compare_images(
                mean_fail,
                reference,
                changed_pixel_threshold=255,
                max_mean_difference=0.1,
                max_changed_fraction=1,
            )
        self.assertFalse(caught.exception.evidence["pass"])

        fraction_fail = reference.copy()
        fraction_fail.putpixel((0, 0), 120)
        fraction_fail.putpixel((1, 0), 120)
        with self.assertRaises(VerificationFailure) as caught:
            compare_images(
                fraction_fail,
                reference,
                changed_pixel_threshold=10,
                max_mean_difference=255,
                max_changed_fraction=0.01,
            )
        self.assertEqual(
            caught.exception.evidence["changed_pixel_fraction"],
            0.02,
        )

        first = compare_images(
            identical,
            reference,
            changed_pixel_threshold=10,
            max_mean_difference=0,
            max_changed_fraction=0,
        )
        second = compare_images(
            identical,
            reference,
            changed_pixel_threshold=10,
            max_mean_difference=0,
            max_changed_fraction=0,
        )
        self.assertEqual(json.dumps(first), json.dumps(second))

    def test_r4_diff_image_is_deterministic_and_sensitive(self):
        reference = Image.new("L", (5, 4), 100)
        current = Image.new("L", (5, 4), 110)
        path = write_diff_image(
            current,
            reference,
            self.root / "diff.png",
        )
        first = path.read_bytes()
        with Image.open(path) as image:
            self.assertEqual(image.size, (10, 4))
        self.assertTrue(first)

        same_path = write_diff_image(
            current,
            reference,
            self.root / "diff2.png",
        )
        self.assertEqual(first, same_path.read_bytes())

        changed = current.copy()
        changed.putpixel((0, 0), 200)
        changed_path = write_diff_image(
            changed,
            reference,
            self.root / "diff3.png",
        )
        self.assertNotEqual(first, changed_path.read_bytes())

    def test_r5_front_top_projection_and_camera_validation(self):
        front = project_points(
            ((0, 0, 0), (2, 0, 0), (0, 0, 2)),
            self.front_camera(),
            100,
            100,
        )
        self.assertGreater(front[1][0], front[0][0])
        self.assertLess(front[2][1], front[0][1])

        top = project_points(
            ((0, 0, 0), (2, 0, 0), (0, 2, 0)),
            self.top_camera(),
            100,
            100,
        )
        self.assertGreater(top[1][0], top[0][0])
        self.assertLess(top[2][1], top[0][1])

        bottom = OrthographicCamera(
            target=(0, 0, 0),
            yaw_deg=0,
            pitch_deg=90,
            distance=10,
        )
        points = project_points(((0, 1, 0),), bottom, 100, 100)
        self.assertTrue(all(map(lambda v: abs(v) < 1000, points[0])))

        with self.assertRaises(VerificationConfigError):
            OrthographicCamera((0, 0, 0), 0, 0, 0)

    def test_r6_expected_box_drawing_is_stable(self):
        base = Image.new("RGB", (100, 100), "white")
        box = ExpectedBox((-2, -1, -2), (2, 1, 2), "box")
        first = draw_expected_geometry(
            base,
            self.front_camera(),
            boxes=(box,),
            labels=False,
        )
        second = draw_expected_geometry(
            base,
            self.front_camera(),
            boxes=(box,),
            labels=False,
        )
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertNotEqual(first.tobytes(), base.tobytes())

        two = draw_expected_geometry(
            base,
            self.front_camera(),
            boxes=(
                box,
                ExpectedBox((4, -1, -1), (6, 1, 1)),
            ),
        )
        self.assertNotEqual(two.tobytes(), first.tobytes())

        projected = project_points(
            ((-2, -1, -2), (2, -1, 2)),
            self.front_camera(),
            100,
            100,
        )
        self.assertAlmostEqual(projected[0][0], 40.0)
        self.assertAlmostEqual(projected[0][1], 60.0)
        self.assertAlmostEqual(projected[1][0], 60.0)
        self.assertAlmostEqual(projected[1][1], 40.0)

    def test_r7_through_hole_slot_and_invalid_features(self):
        base = Image.new("RGB", (120, 120), "white")
        hole = ThroughHole(
            center=(0, 0),
            diameter=4,
            z_min=-2,
            z_max=2,
        )
        slot = ThroughSlot(
            start=(-3, 0),
            end=(3, 0),
            width=2,
            z_min=-2,
            z_max=2,
        )
        hole_image = draw_expected_geometry(
            base,
            self.top_camera(),
            features=(hole,),
        )
        slot_image = draw_expected_geometry(
            base,
            self.top_camera(),
            features=(slot,),
        )
        self.assertNotEqual(hole_image.tobytes(), base.tobytes())
        self.assertNotEqual(slot_image.tobytes(), base.tobytes())

        center = project_points(
            ((0, 0, 0),),
            self.top_camera(),
            120,
            120,
        )[0]
        nearby = hole_image.getpixel(
            (int(center[0] + 12), int(center[1]))
        )
        self.assertNotEqual(nearby, (255, 255, 255))

        with self.assertRaises(VerificationConfigError):
            ThroughSlot(
                start=(0, 0),
                end=(0, 0),
                width=2,
                z_min=0,
                z_max=1,
            )

        with self.assertRaises(VerificationConfigError):
            draw_expected_geometry(
                base,
                self.top_camera(),
                features=(object(),),
            )

    def test_r7b_path_slot_two_point_equivalence_and_curved_path(self):
        base = Image.new("RGB", (140, 140), "white")
        straight = ThroughSlot(
            start=(-4, 0),
            end=(4, 0),
            width=2,
            z_min=-1,
            z_max=1,
        )
        path_straight = ThroughPathSlot(
            centerline=((-4, 0), (4, 0)),
            width=2,
            z_min=-1,
            z_max=1,
        )
        straight_image = draw_expected_geometry(
            base,
            self.top_camera(),
            features=(straight,),
        )
        path_straight_image = draw_expected_geometry(
            base,
            self.top_camera(),
            features=(path_straight,),
        )
        self.assertEqual(
            straight_image.tobytes(),
            path_straight_image.tobytes(),
        )

        curved = ThroughPathSlot(
            centerline=((-4, 0), (0, 3), (4, 0)),
            width=2,
            z_min=-1,
            z_max=1,
            label="curved",
        )
        curved_image = draw_expected_geometry(
            base,
            self.top_camera(),
            features=(curved,),
        )
        self.assertNotEqual(curved_image.tobytes(), base.tobytes())
        self.assertNotEqual(
            curved_image.tobytes(),
            straight_image.tobytes(),
        )

        for centerline in (
            ((0, 0),),
            ((0, 0), (0, 0)),
        ):
            with self.subTest(centerline=centerline):
                with self.assertRaises(VerificationConfigError):
                    ThroughPathSlot(
                        centerline=centerline,
                        width=2,
                        z_min=0,
                        z_max=1,
                    )

        with self.assertRaises(VerificationConfigError):
            ThroughPathSlot(
                centerline=((0, 0), (1, 1)),
                width=0,
                z_min=0,
                z_max=1,
            )
        with self.assertRaises(VerificationConfigError):
            ThroughPathSlot(
                centerline=((0, 0), (1, 1)),
                width=2,
                z_min=2,
                z_max=1,
            )

    def test_r7c_path_slot_is_supported_by_single_view_verification(self):
        actual = self.write_image(
            "path-actual.png",
            "RGB",
            (100, 100),
            "white",
        )
        goal = self.root / "path-goal.png"
        overlay = self.root / "path-overlay.png"
        evidence = verify_visual_view(
            actual,
            actual_reference="actual.png",
            baseline_path=None,
            normalized_size=(50, 50),
            changed_pixel_threshold=12,
            max_mean_difference=6,
            max_changed_fraction=0.08,
            diff_path=None,
            camera=self.top_camera(),
            features=(
                ThroughPathSlot(
                    centerline=((-3, 0), (0, 3), (3, 0)),
                    width=2,
                    z_min=-1,
                    z_max=1,
                ),
            ),
            goal_path=goal,
            goal_reference="goal.png",
            overlay_path=overlay,
            overlay_reference="overlay.png",
        )
        self.assertEqual(evidence.baseline_status, "missing")
        self.assertEqual(evidence.expected_shape_status, "pass")
        self.assertTrue(goal.is_file())
        self.assertTrue(overlay.is_file())

    def test_r8_goal_and_overlay_preserve_distinct_information(self):
        box = ExpectedBox((-2, -2, -2), (2, 2, 2))
        actual = Image.new("RGB", (100, 100), (20, 30, 40))
        goal = make_goal_image(
            (100, 100),
            self.front_camera(),
            boxes=(box,),
        )
        overlay = make_overlay_image(
            actual,
            self.front_camera(),
            boxes=(box,),
        )
        self.assertNotEqual(
            goal.tobytes(),
            Image.new("RGB", (100, 100), "white").tobytes(),
        )
        self.assertNotEqual(overlay.tobytes(), actual.tobytes())
        self.assertEqual(overlay.getpixel((0, 0)), (20, 30, 40))

        goal2 = make_goal_image(
            (100, 100),
            self.front_camera(),
            boxes=(box,),
        )
        self.assertEqual(goal.tobytes(), goal2.tobytes())

    def test_r9_visual_view_evidence_distinguishes_missing_data(self):
        complete = VisualViewEvidence(
            actual_image="actual.png",
            baseline_status="pass",
            regression={"pass": True},
            diff_image="diff.png",
            goal_image="goal.png",
            overlay_image="overlay.png",
            expected_shape_status="pass",
        )
        evidence = complete.to_evidence()
        self.assertEqual(evidence["baseline_status"], "pass")
        self.assertEqual(evidence["expected_shape_status"], "pass")

        failed = VisualViewEvidence(
            actual_image="actual.png",
            baseline_status="fail",
            regression={"pass": False},
            expected_shape_status="pass",
        ).to_evidence()
        self.assertEqual(failed["baseline_status"], "fail")

        missing_baseline = VisualViewEvidence(
            actual_image="actual.png",
            baseline_status="missing",
            expected_shape_status="pass",
        ).to_evidence()
        self.assertEqual(missing_baseline["baseline_status"], "missing")
        self.assertIsNone(missing_baseline["regression"])

        missing_outputs = VisualViewEvidence(
            actual_image=None,
            baseline_status="missing",
            goal_image=None,
            overlay_image=None,
            expected_shape_status="missing",
        ).to_evidence()
        self.assertIsNone(missing_outputs["actual_image"])
        self.assertIsNone(missing_outputs["goal_image"])
        self.assertIsNone(missing_outputs["overlay_image"])
        self.assertEqual(
            missing_outputs["expected_shape_status"],
            "missing",
        )

    def test_r11_verify_visual_view_passes_and_writes_all_artifacts(self):
        actual = self.write_image(
            "actual.png",
            "RGB",
            (80, 60),
            (100, 100, 100),
        )
        baseline = self.write_image(
            "baseline.png",
            "RGB",
            (80, 60),
            (100, 100, 100),
        )
        diff = self.root / "out" / "diff.png"
        goal = self.root / "out" / "goal.png"
        overlay = self.root / "out" / "overlay.png"

        evidence = verify_visual_view(
            actual,
            actual_reference="evidence/actual.png",
            baseline_path=baseline,
            normalized_size=(40, 30),
            changed_pixel_threshold=12,
            max_mean_difference=0,
            max_changed_fraction=0,
            diff_path=diff,
            diff_reference="evidence/diff.png",
            camera=self.front_camera(),
            boxes=(ExpectedBox((-2, -1, -2), (2, 1, 2)),),
            goal_path=goal,
            goal_reference="evidence/goal.png",
            overlay_path=overlay,
            overlay_reference="evidence/overlay.png",
        )

        self.assertEqual(evidence.baseline_status, "pass")
        self.assertEqual(evidence.expected_shape_status, "pass")
        self.assertEqual(evidence.actual_image, "evidence/actual.png")
        self.assertEqual(evidence.diff_image, "evidence/diff.png")
        self.assertEqual(evidence.goal_image, "evidence/goal.png")
        self.assertEqual(evidence.overlay_image, "evidence/overlay.png")
        self.assertEqual(evidence.regression["pass"], True)
        self.assertTrue(diff.is_file())
        self.assertTrue(goal.is_file())
        self.assertTrue(overlay.is_file())

    def test_r12_visual_view_mismatch_preserves_complete_evidence(self):
        actual = self.write_image(
            "actual-fail.png",
            "RGB",
            (20, 20),
            (200, 200, 200),
        )
        baseline = self.write_image(
            "baseline-fail.png",
            "RGB",
            (20, 20),
            (100, 100, 100),
        )
        diff = self.root / "fail" / "diff.png"
        goal = self.root / "fail" / "goal.png"
        overlay = self.root / "fail" / "overlay.png"

        with self.assertRaises(VerificationFailure) as caught:
            verify_visual_view(
                actual,
                actual_reference="actual-ref",
                baseline_path=baseline,
                normalized_size=(20, 20),
                changed_pixel_threshold=1,
                max_mean_difference=0,
                max_changed_fraction=0,
                diff_path=diff,
                diff_reference="diff-ref",
                camera=self.front_camera(),
                boxes=(ExpectedBox((-1, -1, -1), (1, 1, 1)),),
                goal_path=goal,
                goal_reference="goal-ref",
                overlay_path=overlay,
                overlay_reference="overlay-ref",
            )

        evidence = caught.exception.evidence
        self.assertEqual(evidence["baseline_status"], "fail")
        self.assertEqual(evidence["expected_shape_status"], "pass")
        self.assertEqual(evidence["actual_image"], "actual-ref")
        self.assertEqual(evidence["diff_image"], "diff-ref")
        self.assertEqual(evidence["goal_image"], "goal-ref")
        self.assertEqual(evidence["overlay_image"], "overlay-ref")
        self.assertFalse(evidence["regression"]["pass"])
        self.assertTrue(diff.is_file())
        self.assertTrue(goal.is_file())
        self.assertTrue(overlay.is_file())

    def test_r13_visual_view_missing_baseline_is_explicit(self):
        actual = self.write_image(
            "actual-missing.png",
            "RGB",
            (20, 20),
            (100, 100, 100),
        )
        diff = self.root / "missing" / "diff.png"

        evidence = verify_visual_view(
            actual,
            actual_reference="actual",
            baseline_path=self.root / "not-approved.png",
            normalized_size=(10, 10),
            changed_pixel_threshold=12,
            max_mean_difference=6,
            max_changed_fraction=0.08,
            diff_path=diff,
        )

        self.assertEqual(evidence.baseline_status, "missing")
        self.assertIsNone(evidence.regression)
        self.assertIsNone(evidence.diff_image)
        self.assertEqual(evidence.expected_shape_status, "missing")
        self.assertFalse(diff.exists())

    def test_r14_visual_view_configuration_is_explicit(self):
        actual = self.write_image(
            "actual-config.png",
            "RGB",
            (20, 20),
            (100, 100, 100),
        )
        baseline = self.write_image(
            "baseline-config.png",
            "RGB",
            (20, 20),
            (100, 100, 100),
        )
        box = ExpectedBox((-1, -1, -1), (1, 1, 1))

        with self.assertRaisesRegex(
            VerificationConfigError,
            "diff_path is required",
        ):
            verify_visual_view(
                actual,
                actual_reference=None,
                baseline_path=baseline,
                normalized_size=(10, 10),
                changed_pixel_threshold=12,
                max_mean_difference=6,
                max_changed_fraction=0.08,
                diff_path=None,
            )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "expected geometry requires a camera",
        ):
            verify_visual_view(
                actual,
                actual_reference=None,
                normalized_size=(10, 10),
                changed_pixel_threshold=12,
                max_mean_difference=6,
                max_changed_fraction=0.08,
                diff_path=self.root / "unused.png",
                boxes=(box,),
            )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "camera requires expected geometry",
        ):
            verify_visual_view(
                actual,
                actual_reference=None,
                normalized_size=(10, 10),
                changed_pixel_threshold=12,
                max_mean_difference=6,
                max_changed_fraction=0.08,
                diff_path=self.root / "unused.png",
                camera=self.front_camera(),
                goal_path=self.root / "goal.png",
                overlay_path=self.root / "overlay.png",
            )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "goal_path and overlay_path are required",
        ):
            verify_visual_view(
                actual,
                actual_reference=None,
                normalized_size=(10, 10),
                changed_pixel_threshold=12,
                max_mean_difference=6,
                max_changed_fraction=0.08,
                diff_path=self.root / "unused.png",
                camera=self.front_camera(),
                boxes=(box,),
            )

    def test_r10_module_contains_no_consumer_or_view_policy(self):
        source = inspect.getsource(visual_module).lower()
        forbidden = (
            "solidcraft",
            "cadcraft",
            "forge",
            "front_view",
            "top_view",
            "iso_view",
            "required_views",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)


if __name__ == "__main__":
    unittest.main()
