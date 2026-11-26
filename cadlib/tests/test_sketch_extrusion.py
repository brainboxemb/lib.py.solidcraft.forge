"""Sketch contract tests."""
import unittest

from scpf import (
    Anchor,
    Axis,
    Box,
    CENTER,
    Rectangle2D,
    RoundedRectangle2D,
    Circle2D,
    Depth,
    Edges,
    Sketch,
    Parameter,
    Polygon2D,
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


    def test_standalone_sketch_extrusion_is_native_boolean_operand(self):
        base = Box(120, 100, 40)

        with Sketch(name="Rear recess", plane="YZ") as sketch:
            sketch.add(
                RoundedRectangle2D(70, 80, 10),
                offset=(5, 0),
            )
        operand = sketch.extrude(14, sym=True)

        for expression, expected_operation in (
            (base + operand, "join"),
            (base - operand, "cut"),
            (base & operand, "intersect"),
        ):
            with self.subTest(operation=expected_operation):
                commands = compile_model(
                    expression,
                    f"Standalone_{expected_operation}",
                )["commands"]
                extrude = [
                    row for row in commands
                    if row["command"] == "solid.extrude"
                ][-1]
                self.assertEqual(
                    extrude["params"]["operation"],
                    expected_operation,
                )
                self.assertEqual(
                    extrude["params"]["targets"],
                    [f"Standalone_{expected_operation}"],
                )
                self.assertEqual(
                    extrude["params"]["direction"],
                    "symmetric",
                )
                self.assertEqual(extrude["params"]["distance"], 14)
                self.assertNotIn("body_name", extrude["params"])

                sketch_create = next(
                    row for row in commands
                    if row["command"] == "sketch.create"
                )
                self.assertEqual(
                    sketch_create["params"]["plane"],
                    "YZ",
                )

    def test_root_standalone_sketch_extrusion_remains_new_body(self):
        with Sketch(name="Standalone", plane="XY") as sketch:
            Rectangle2D(20, 10)
        commands = compile_model(sketch.extrude(5), "Standalone")["commands"]
        extrude = commands[-1]["params"]
        self.assertEqual(extrude["body_name"], "Standalone")
        self.assertNotIn("operation", extrude)
        self.assertNotIn("targets", extrude)

    def test_root_standalone_sketch_revolve_is_native_new_body(self):
        sweep = Parameter("sweep", 180)
        with Sketch(name="RivetProfile", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 2), (6, 2), (6, 0)],
                plane="XZ",
            )

        commands = compile_model(
            sketch.revolve(axis=Axis.X, angle=sweep),
            "Rivet",
        )["commands"]

        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units["sweep"], "deg")

        revolve = commands[-1]
        self.assertEqual(revolve["command"], "solid.revolve")
        self.assertEqual(
            revolve["params"],
            {
                "sketch": "RivetProfile",
                "axis": "X",
                "angle": "sweep",
                "body_name": "Rivet",
            },
        )

    def test_standalone_sketch_revolve_is_native_boolean_operand(self):
        base = Box(40, 40, 20)
        with Sketch(name="TurnedFeature", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 2), (8, 2), (8, 0)],
                plane="XZ",
            )
        operand = sketch.revolve(axis=Axis.X, angle=120, sym=True)

        for expression, expected_operation in (
            (base + operand, "join"),
            (base - operand, "cut"),
            (base & operand, "intersect"),
        ):
            with self.subTest(operation=expected_operation):
                commands = compile_model(
                    expression,
                    f"Revolve_{expected_operation}",
                )["commands"]
                revolve = [
                    row for row in commands
                    if row["command"] == "solid.revolve"
                ][-1]
                self.assertEqual(
                    revolve["params"]["operation"],
                    expected_operation,
                )
                self.assertEqual(
                    revolve["params"]["targets"],
                    [f"Revolve_{expected_operation}"],
                )
                self.assertEqual(revolve["params"]["axis"], "X")
                self.assertEqual(revolve["params"]["angle"], 120)
                self.assertEqual(revolve["params"]["direction"], "symmetric")
                self.assertNotIn("body_name", revolve["params"])

    def test_shifted_axis_revolve_keeps_symbolic_native_axis_and_one_cut(self):
        from scpf import AxisLine
        from scpf.core import Parameter

        pin_x = Parameter("pin_x", 8)
        pin_z = Parameter("pin_z", 3)
        relief_d = Parameter("relief_d", 4.5)
        core_d = Parameter("core_d", 3.7)

        with Sketch(name="Pass through", plane="XY", offset=pin_z) as sketch:
            Polygon2D(
                [
                    (pin_x, -12),
                    (pin_x + relief_d / 2, -12),
                    (pin_x + relief_d / 2, -9),
                    (pin_x + core_d / 2, -9),
                    (pin_x + core_d / 2, 9),
                    (pin_x + relief_d / 2, 9),
                    (pin_x + relief_d / 2, 12),
                    (pin_x, 12),
                ],
                plane="XY",
            )
        cut = sketch.revolve(
            axis=AxisLine(Axis.Y, origin=(pin_x, 0, pin_z))
        )

        commands = compile_model(
            Box(40, 24, 20) - cut,
            "Panel",
        )["commands"]
        revolve = next(
            row for row in commands
            if row["command"] == "solid.revolve"
        )
        self.assertEqual(
            revolve["params"]["axis"],
            {
                "origin": ["pin_x", 0, "pin_z"],
                "dir": [0.0, 1.0, 0.0],
            },
        )
        self.assertEqual(revolve["params"]["operation"], "cut")
        self.assertEqual(revolve["params"]["targets"], ["Panel"])
        self.assertEqual(
            sum(row["command"] == "solid.revolve" for row in commands),
            1,
        )

    def test_shifted_axis_revolve_requires_axis_coplanar_with_sketch(self):
        from scpf import AxisLine
        from scpf.core import Parameter

        plane_z = Parameter("plane_z", 3)
        with Sketch(name="Profile", plane="XY", offset=plane_z) as sketch:
            Polygon2D([(0, -2), (2, -2), (2, 2), (0, 2)], plane="XY")

        with self.assertRaisesRegex(ValueError, "direction must lie"):
            sketch.revolve(
                axis=AxisLine(Axis.Z, origin=(0, 0, plane_z))
            )
        with self.assertRaisesRegex(ValueError, "origin must lie"):
            sketch.revolve(
                axis=AxisLine(Axis.Y, origin=(0, 0, 4))
            )
        with self.assertRaisesRegex(ValueError, "requires AxisLine"):
            sketch.revolve(axis=Axis.Y)

    def test_sketch_revolve_validates_world_axis_plane_and_sweep(self):
        with Sketch(name="Profile", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 2), (6, 2), (6, 0)],
                plane="XZ",
            )

        with self.assertRaisesRegex(ValueError, "lie in the Sketch plane"):
            sketch.revolve(axis=Axis.Y)
        with self.assertRaisesRegex(ValueError, "above 0 and at most 360"):
            sketch.revolve(axis=Axis.X, angle=0)
        with self.assertRaisesRegex(ValueError, "above 0 and at most 360"):
            sketch.revolve(axis=Axis.X, angle=361)
        with self.assertRaisesRegex(TypeError, "True or False"):
            sketch.revolve(axis=Axis.X, sym="yes")
        with self.assertRaisesRegex(ValueError, "Axis.X, Axis.Y or Axis.Z"):
            sketch.revolve(axis="X")

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

    def test_connected_profile_lowers_native_line_and_arc_commands(self):
        width = Parameter("width", 40)
        with Sketch(name="Mixed", plane="XY") as sketch:
            contour = sketch.profile(start=(0, 0))
            contour.line_to((width, 0))
            contour.arc_through_to(
                (width, 20),
                through=(width + 10, 10),
            )
            contour.line_to((0, 20))
            contour.line_to((0, 0))
            contour.close()

        commands = compile_model(sketch.extrude(8), "Mixed")["commands"]
        native = [
            row for row in commands
            if row["command"].startswith("sketch.")
        ]
        self.assertEqual(
            [row["command"] for row in native],
            [
                "sketch.create",
                "sketch.line",
                "sketch.arc.three_point",
                "sketch.line",
                "sketch.line",
                "sketch.finish",
            ],
        )
        for row in native[1:-1]:
            self.assertTrue(row["params"]["connect"])

        first = native[1]["params"]["points"]
        arc = native[2]["params"]
        self.assertEqual(first[0], [0, 0])
        self.assertEqual(first[1], ["width", 0])
        self.assertEqual(arc["start"], ["width", 0])
        self.assertEqual(arc["end"], ["width", 20])
        self.assertIn("width", str(arc["through"][0]))

    def test_connected_profile_center_arc_and_attached_lowering_share_native_form(self):
        base = Box(100, 80, 5, anchor=Anchor.BOTTOM)
        with Sketch(name="MixedCut", on=base, parent=Anchor.TOP) as sketch:
            contour = sketch.profile(start=(-20, 0))
            contour.line_to((-10, -10))
            contour.arc_center_to(
                (10, -10),
                center=(0, -10),
                clockwise=True,
            )
            contour.line_to((20, 0))
            contour.line_to((-20, 0))
            contour.close()

        commands = compile_model(
            base - sketch.extrude(5),
            "MixedCut",
        )["commands"]
        arc = next(
            row for row in commands
            if row["command"] == "sketch.arc.center_point"
        )
        self.assertTrue(arc["params"]["clockwise"])
        self.assertTrue(arc["params"]["connect"])
        self.assertIn("sketch.line", [row["command"] for row in commands])

    def test_connected_profile_requires_explicit_valid_closure(self):
        with self.assertRaisesRegex(ValueError, "must be closed"):
            with Sketch(name="Open", plane="XY") as sketch:
                contour = sketch.profile(start=(0, 0))
                contour.line_to((10, 0))

        with Sketch(name="InvalidClose", plane="XY") as sketch:
            contour = sketch.profile(start=(0, 0))
            contour.line_to((10, 0))
            contour.line_to((10, 10))
            with self.assertRaisesRegex(ValueError, "final endpoint"):
                contour.close()
            contour.line_to((0, 0))
            contour.close()

        with Sketch(name="Degenerate", plane="XY") as sketch:
            contour = sketch.profile(start=(0, 0))
            with self.assertRaisesRegex(ValueError, "non-zero"):
                contour.line_to((0, 0))
            contour.line_to((10, 0))
            contour.line_to((0, 0))
            contour.close()

    def test_empty_sketch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one profile"):
            with Sketch(plane="XY"):
                pass


if __name__ == "__main__":
    unittest.main()
