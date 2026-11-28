"""Backend-independent contracts for Forge CAD semantic normalization."""
import unittest

from scpf import (
    Axis,
    AxisLine,
    Box,
    Parameter,
    Polygon2D,
    Sketch,
)
from scpf.ir import (
    AxisLineIR,
    BoxIR,
    LegacyShapeIR,
    PlacementIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    normalize_shape,
)


class IRNormalizationTests(unittest.TestCase):
    def test_principal_revolve_normalizes_to_semantic_axis_line(self):
        length = Parameter("length", 10)
        radius = Parameter("radius", 4)
        sweep = Parameter("sweep", 360)
        with Sketch(name="RadialProfile", plane="XZ") as sketch:
            Polygon2D(
                [
                    (0, 0),
                    (0, radius),
                    (length, radius),
                    (length, 0),
                ],
                plane="XZ",
            )

        model = normalize_shape(
            sketch.revolve(axis=Axis.X, angle=sweep)
        )

        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            model.root.axis,
            AxisLineIR(direction="X", origin=(0, 0, 0)),
        )
        self.assertEqual(model.root.operation, "new_body")
        self.assertIsNone(model.root.target)
        self.assertEqual(model.root.region, RegionIR(outer=0))
        self.assertIsInstance(
            model.root.sketch.profiles[0],
            PolygonProfileIR,
        )
        self.assertEqual(
            [(parameter.name, parameter.unit) for parameter in model.parameters],
            [
                ("radius", "mm"),
                ("length", "mm"),
                ("sweep", "deg"),
            ],
        )

    def test_shifted_axis_revolve_cut_preserves_feature_and_parameter_intent(self):
        axis_x = Parameter("axis_x", 8)
        panel = Box(80, 46, 10)
        with Sketch(name="PassThrough", plane="XY") as profile:
            Polygon2D(
                [
                    (12, -5),
                    (16, -5),
                    (16, 5),
                    (12, 5),
                ],
                plane="XY",
            )

        cut = profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(axis_x, 0, 0),
            ),
        )
        model = normalize_shape(panel - cut)

        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(model.root.operation, "cut")
        self.assertIsInstance(model.root.target, PlacementIR)
        self.assertIsInstance(model.root.target.primitive, BoxIR)
        self.assertEqual(
            model.root.axis,
            AxisLineIR(
                direction="Y",
                origin=(axis_x, 0, 0),
            ),
        )
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["axis_x"],
        )
        self.assertNotIsInstance(model.root, LegacyShapeIR)

    def test_non_principal_custom_axis_stays_outside_bounded_ir_slice(self):
        with Sketch(name="DiagonalAxis", plane="XY") as profile:
            Polygon2D(
                [
                    (12, -5),
                    (16, -5),
                    (16, 5),
                    (12, 5),
                ],
                plane="XY",
            )

        shape = profile.revolve(
            axis=AxisLine(
                (1, 1, 0),
                origin=(0, 0, 0),
            ),
        )
        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)


if __name__ == "__main__":
    unittest.main()
