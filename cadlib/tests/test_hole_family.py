"""Public API and compiler contracts for the native Hole family."""

import unittest

from scpf import (
    Anchor,
    Box,
    CounterboreHole,
    CountersinkHole,
    Hole,
    ThreadedHole,
)
from scpf.compiler import compile_model


class HoleFamilyTests(unittest.TestCase):
    def test_all_hole_variants_lower_one_to_one_to_native_hole(self):
        body = Box(120, 40, 12, anchor=Anchor.BOTTOM)
        features = (
            Hole(d=6, direction=(0, 0, -1)),
            CounterboreHole(
                d=6,
                counterbore_d=12,
                counterbore_depth=4,
                direction=(0, 0, -1),
            ),
            CountersinkHole(
                d=6,
                countersink_d=12,
                countersink_angle=90,
                direction=(0, 0, -1),
            ),
            ThreadedHole(
                thread="M6",
                d=5,
                direction=(0, 0, -1),
                thread_depth=10,
                modeled=True,
                ease_out="short",
            ),
        )
        for x, feature in zip((-45, -15, 15, 45), features):
            body = body + feature.at(x, 0, 12)

        commands = compile_model(body, "HoleFamily")["commands"]
        holes = [
            row["params"]
            for row in commands
            if row["command"] == "solid.hole"
        ]
        self.assertEqual(len(holes), 4)
        self.assertEqual(
            [row.get("type", "simple") for row in holes],
            ["simple", "counterbore", "countersink", "simple"],
        )
        self.assertEqual(holes[1]["cb_diameter"], 12)
        self.assertEqual(holes[1]["cb_depth"], 4)
        self.assertEqual(holes[2]["cs_diameter"], 12)
        self.assertEqual(holes[2]["cs_angle"], 90)
        self.assertEqual(holes[3]["thread"], "M6")
        self.assertEqual(holes[3]["thread_depth"], 10)
        self.assertTrue(holes[3]["modeled"])
        self.assertEqual(holes[3]["ease_out"], "short")

    def test_hole_family_validates_feature_specific_dimensions(self):
        with self.assertRaises(ValueError):
            Hole(d=0)
        with self.assertRaises(ValueError):
            CounterboreHole(
                d=6,
                counterbore_d=6,
                counterbore_depth=3,
            )
        with self.assertRaises(ValueError):
            CounterboreHole(
                d=6,
                counterbore_d=10,
                counterbore_depth=0,
            )
        with self.assertRaises(ValueError):
            CountersinkHole(d=6, countersink_d=6)
        with self.assertRaises(ValueError):
            CountersinkHole(
                d=6,
                countersink_d=10,
                countersink_angle=180,
            )
        with self.assertRaises(ValueError):
            ThreadedHole(thread="")
        with self.assertRaises(ValueError):
            ThreadedHole(thread="M6", hand="clockwise")
        with self.assertRaises(ValueError):
            ThreadedHole(thread="M6", thread_depth=0)
        with self.assertRaises(ValueError):
            ThreadedHole(thread="M6", ease_out="medium")

    def test_threaded_hole_keeps_cosmetic_and_modeled_intent_distinct(self):
        body = Box(30, 30, 12, anchor=Anchor.BOTTOM)

        cosmetic = compile_model(
            body + ThreadedHole(
                thread="M6",
                d=5,
                direction=(0, 0, -1),
            ).at(0, 0, 12),
            "Cosmetic",
        )["commands"][-1]["params"]
        modeled = compile_model(
            body + ThreadedHole(
                thread="M6",
                d=5,
                direction=(0, 0, -1),
                modeled=True,
            ).at(0, 0, 12),
            "Modeled",
        )["commands"][-1]["params"]

        self.assertEqual(cosmetic["thread"], "M6")
        self.assertNotIn("modeled", cosmetic)
        self.assertEqual(modeled["thread"], "M6")
        self.assertTrue(modeled["modeled"])


if __name__ == "__main__":
    unittest.main()
