"""Headless replay transport tests."""

import unittest

from scpf.headless import (
    HeadlessReplayError,
    _active_sketch_after,
    _phase_commands,
)


class HeadlessSketchReplayTests(unittest.TestCase):
    def test_next_phase_reopens_active_sketch_by_native_feature_id(self):
        chunk = [{
            "command": "sketch.pattern.rectangular",
            "params": {
                "entities": "$seed_curves",
                "count": 3,
                "spacing": 20,
            },
        }]
        native, prefix = _phase_commands(
            chunk,
            {"$seed_curves": ["circle1"]},
            17,
        )

        self.assertEqual(prefix, 1)
        self.assertEqual(
            native[0],
            {"command": "sketch.edit", "params": {"sketch": 17}},
        )
        self.assertEqual(native[1]["params"]["entities"], ["circle1"])

    def test_create_result_opens_and_finish_closes_tracked_sketch(self):
        active = _active_sketch_after(
            [
                {"command": "sketch.create", "params": {"name": "Pattern"}},
                {"command": "sketch.circle.center", "params": {"center": [0, 0]}},
            ],
            [
                {"sketch": 23, "name": "Pattern"},
                {"curves": ["circle1"]},
            ],
            None,
        )
        self.assertEqual(active, 23)

        active = _active_sketch_after(
            [{"command": "sketch.finish", "params": {}}],
            [{}],
            active,
        )
        self.assertIsNone(active)

    def test_create_must_return_native_sketch_id(self):
        with self.assertRaisesRegex(
            HeadlessReplayError,
            "did not return a sketch id",
        ):
            _active_sketch_after(
                [{"command": "sketch.create", "params": {"name": "Pattern"}}],
                [{"name": "Pattern"}],
                None,
            )


if __name__ == "__main__":
    unittest.main()
