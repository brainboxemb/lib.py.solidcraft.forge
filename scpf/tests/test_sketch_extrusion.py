"""Sketch contract tests."""
import unittest

from scpf import (
    Anchor,
    Box,
    CENTER,
    Rectangle2D,
    Circle2D,
    Depth,
    Edges,
    Sketch,
    Parameter,
)
from scpf.compiler import ModelError, compile_model

class SketchExtrusionTests(unittest.TestCase):
    def test_sketch_extrude_signed_distance_and_sym(self):
        height = Parameter("height", 30)
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)

        positive = compile_model(sketch.extrude(height), "Positive")["commands"][-1]["params"]
        negative = compile_model(sketch.extrude(-height), "Negative")["commands"][-1]["params"]
        symmetric = compile_model(
            sketch.extrude(height, sym=True), "Symmetric"
        )["commands"][-1]["params"]

        self.assertEqual(positive["distance"], "height")
        self.assertEqual(positive["direction"], "positive")
        self.assertEqual(negative["distance"], "height")
        self.assertEqual(negative["direction"], "negative")
        self.assertEqual(symmetric["distance"], "height")
        self.assertEqual(symmetric["direction"], "symmetric")

        with self.assertRaisesRegex(ValueError, "non-zero"):
            sketch.extrude(0)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            sketch.extrude(-10, sym=True)
        with self.assertRaisesRegex(TypeError, "True or False"):
            sketch.extrude(10, sym="yes")

    def test_sketch_extrude_profile_points_lower_for_standalone_and_attached(self):
        with Sketch(name="Standalone", plane="XY") as standalone:
            Circle2D(d=20)
        standalone_extrude = compile_model(
            standalone.extrude(
                10,
                profiles=[(0, 0)],
                exact_regions=True,
            ),
            "StandaloneSelected",
        )["commands"][-1]["params"]
        self.assertEqual(
            standalone_extrude["profiles"],
            [{"point": [0.0, 0.0]}],
        )
        self.assertTrue(standalone_extrude["exact_regions"])

        base = Box(80, 60, 5, anchor=Anchor.BOTTOM)
        with Sketch(name="Attached", on=base, parent=Anchor.TOP) as attached:
            attached.add(Circle2D(d=10), offset=(-15, 0))
            attached.add(Circle2D(d=10), offset=(15, 0))
        commands = compile_model(
            base - attached.extrude(
                Depth.THROUGH_ALL,
                profiles=[(-15, 0)],
                exact_regions=True,
            ),
            "AttachedSelected",
        )["commands"]
        attached_extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertEqual(
            attached_extrude["profiles"],
            [{"point": [-15.0, 0.0]}],
        )
        self.assertTrue(attached_extrude["exact_regions"])

    def test_sketch_extrude_default_keeps_all_profiles(self):
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)
        extrude = compile_model(
            sketch.extrude(10),
            "AllProfiles",
        )["commands"][-1]["params"]
        self.assertNotIn("profiles", extrude)
        self.assertNotIn("exact_regions", extrude)

    def test_sketch_extrude_profile_selection_validates_points(self):
        with Sketch(plane="XY") as sketch:
            Circle2D(d=20)

        invalid_profiles = (
            [],
            [(0,)],
            [(0, 0, 0)],
            [("x", 0)],
            [(True, 0)],
            [(float("nan"), 0)],
            [(Parameter("pick", 0), 0)],
        )
        for profiles in invalid_profiles:
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):
                sketch.extrude(10, profiles=profiles)

        with self.assertRaisesRegex(TypeError, "exact_regions"):
            sketch.extrude(10, profiles=[(0, 0)], exact_regions="yes")
        with self.assertRaisesRegex(ValueError, "requires profiles"):
            sketch.extrude(10, exact_regions=True)

    def test_empty_sketch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one profile"):
            with Sketch(plane="XY"):
                pass


if __name__ == "__main__":
    unittest.main()
