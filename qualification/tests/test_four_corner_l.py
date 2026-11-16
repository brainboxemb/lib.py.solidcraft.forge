"""Qualification tests for four vertical L-profiles on rounded side corners."""
import json
import os
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
NATIVE_ROOT = os.environ.get("SCPF_NATIVE_ROOT")


class FourCornerLCommandTests(unittest.TestCase):
    def test_copied_profiles_are_blocked_without_native_copy_reference(self):
        from scpf.compiler import ModelError

        with self.assertRaisesRegex(
            ModelError,
            "cannot attach a copied occurrence",
        ):
            run_script(ROOT / "examples/four-corner-l/scpf/model.py")


@unittest.skip("blocked: copied attachment occurrences have no explicit SolidCraft 0.42 reference")
class FourCornerLNativeTests(unittest.TestCase):
    def test_native_bounding_boxes_match_four_centered_vertical_profiles(self):
        data = _load(
            Path(NATIVE_ROOT) / "four-corner-l" / "measurements.json"
        )
        self.assertEqual(data["body_count"], 5)

        frame = next(
            body for body in data["bodies"]
            if body["name"] == "FrameBlock"
        )
        self.assertEqual(
            _rounded_bbox(frame),
            {
                "min": [-60.0, -40.0, 0.0],
                "max": [60.0, 40.0, 60.0],
            },
        )

        profiles = [
            body for body in data["bodies"]
            if body["name"].startswith("LProfile")
        ]
        self.assertEqual(len(profiles), 4)

        actual = sorted(
            (
                tuple(_rounded_bbox(body)["min"]),
                tuple(_rounded_bbox(body)["max"]),
            )
            for body in profiles
        )
        expected = sorted([
            ((-64.0, -44.0, 22.0), (-32.0, -12.0, 38.0)),
            ((32.0, -44.0, 22.0), (64.0, -12.0, 38.0)),
            ((32.0, 12.0, 22.0), (64.0, 44.0, 38.0)),
            ((-64.0, 12.0, 22.0), (-32.0, 44.0, 38.0)),
        ])
        self.assertEqual(actual, expected)

    def test_saved_size_mutation_moves_profiles_but_keeps_mid_height(self):
        data = _load(
            Path(NATIVE_ROOT)
            / "four-corner-l"
            / "measurements-size-160x120.json"
        )
        self.assertEqual(data["body_count"], 5)
        self.assertEqual(
            _params(data),
            {
                "frame_width": 160.0,
                "frame_depth": 120.0,
                "frame_height": 60.0,
            },
        )

        profiles = [
            body for body in data["bodies"]
            if body["name"].startswith("LProfile")
        ]
        actual = sorted(
            (
                tuple(_rounded_bbox(body)["min"]),
                tuple(_rounded_bbox(body)["max"]),
            )
            for body in profiles
        )
        expected = sorted([
            ((-84.0, -64.0, 22.0), (-52.0, -32.0, 38.0)),
            ((52.0, -64.0, 22.0), (84.0, -32.0, 38.0)),
            ((52.0, 32.0, 22.0), (84.0, 64.0, 38.0)),
            ((-84.0, 32.0, 22.0), (-52.0, 64.0, 38.0)),
        ])
        self.assertEqual(actual, expected)


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _params(measurements):
    return {row["name"]: row["value"] for row in measurements["params"]}


def _rounded_bbox(body):
    return {
        "min": [round(value, 6) for value in body["bbox"]["min"]],
        "max": [round(value, 6) for value in body["bbox"]["max"]],
    }


if __name__ == "__main__":
    unittest.main()
