"""Contracts for the engine-neutral Forge semantic IR boundary."""
import unittest

from scpf import (
    Anchor,
    Box,
    Circle2D,
    Cylinder,
    Edges,
    Faces,
    Parameter,
    Sketch,
    Sphere,
)
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from scpf.ir import (
    BooleanSubtractIR,
    BoxIR,
    ChamferIR,
    CircleExtrudeIR,
    CylinderIR,
    LegacyShapeIR,
    PlacementIR,
    normalize_shape,
)


class SemanticIRTests(unittest.TestCase):
    def assert_solidcraft_compatibility(self, shape, name):
        model = normalize_shape(shape)
        self.assertNotIsInstance(model.root, LegacyShapeIR)
        current = compile_solidcraft_ir(model, name)
        legacy = _compile_shape_legacy_with_dependencies(shape, name)[0]
        self.assertEqual(current, legacy)
        return model

    def test_parameterized_box_is_geometry_plus_placement_ir(self):
        length = Parameter("length", 40)
        width = Parameter("width", 30)
        height = Parameter("height", 10)
        shape = Box(
            length,
            width,
            height,
            anchor=Anchor.BOTTOM,
        )

        model = self.assert_solidcraft_compatibility(shape, "Panel")
        self.assert_solidcraft_compatibility(
            Box(length, width, height, anchor=Anchor.CENTER),
            "CenteredPanel",
        )
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIsInstance(model.root.primitive, BoxIR)
        self.assertEqual(model.root.point, (0, 0, 0))
        self.assertEqual(model.root.anchor, (0, 0, -1))
        self.assertFalse(model.root.explicit)
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["length", "width", "height"],
        )

        mitcad = compile_mitcad_ir(model, "Panel")
        self.assertEqual(mitcad["backend"], "mitcad")
        self.assertEqual(
            [row["cmd"] for row in mitcad["commands"]],
            [
                "add_parameter",
                "add_parameter",
                "add_parameter",
                "add_feature",
            ],
        )

    def test_explicit_box_placement_keeps_solidcraft_commands_and_mitcad_values(self):
        length = Parameter("length", 40)
        width = Parameter("width", 30)
        x = Parameter("x_position", 8)
        y = Parameter("y_position", -5)
        shape = Box(length, width, 10).at(
            x,
            y,
            0,
            anchor=Anchor.BOTTOM,
        )

        model = self.assert_solidcraft_compatibility(shape, "PlacedBox")
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIsInstance(model.root.primitive, BoxIR)
        self.assertEqual(model.root.point, (x, y, 0))
        self.assertEqual(model.root.anchor, (0, 0, -1))
        self.assertTrue(model.root.explicit)

        feature = compile_mitcad_ir(model, "PlacedBox")["commands"][-1]["def"]
        self.assertEqual(feature["type"], "box")
        self.assertIn("x_position", str(feature["corner"][0]))
        self.assertIn("length", str(feature["corner"][0]))
        self.assertIn("y_position", str(feature["corner"][1]))
        self.assertIn("width", str(feature["corner"][1]))

    def test_cylinder_is_geometry_plus_placement_ir(self):
        height = Parameter("height", 30)
        diameter = Parameter("diameter", 10)
        shape = Cylinder(d=diameter, h=height)

        model = self.assert_solidcraft_compatibility(
            shape,
            "CylinderTest",
        )
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIsInstance(model.root.primitive, CylinderIR)
        self.assertEqual(model.root.primitive.axis, "Z")
        self.assertEqual(model.root.point, (0, 0, 0))
        self.assertEqual(model.root.anchor, (0, 0, 0))
        self.assertFalse(model.root.explicit)

        definition = compile_mitcad_ir(
            model,
            "CylinderTest",
        )["commands"][-1]["def"]
        self.assertEqual(definition["type"], "cylinder")
        self.assertEqual(definition["plane"], "xy")
        self.assertEqual(definition["center"], [0, 0])
        self.assertEqual(definition["diameter"], "diameter")
        self.assertEqual(definition["height"], "height")
        self.assertTrue(definition["symmetric"])
        self.assertEqual(definition["operation"], "new_body")

    def test_explicit_cylinder_placement_is_shared_by_both_backends(self):
        diameter = Parameter("diameter", 10)
        height = Parameter("height", 30)
        x = Parameter("x_position", 8)
        y = Parameter("y_position", -5)
        shape = Cylinder(d=diameter, h=height).at(x, y, 0)

        model = self.assert_solidcraft_compatibility(shape, "PlacedCylinder")
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIsInstance(model.root.primitive, CylinderIR)
        self.assertEqual(model.root.point, (x, y, 0))
        self.assertTrue(model.root.explicit)

        definition = compile_mitcad_ir(
            model,
            "PlacedCylinder",
        )["commands"][-1]["def"]
        self.assertEqual(definition["center"], ["x_position", "y_position"])
        self.assertEqual(definition["plane"], "xy")
        self.assertTrue(definition["symmetric"])

    def test_box_minus_placed_cylinder_is_typed_boolean_for_both_backends(self):
        thickness = Parameter("thickness", 12)
        bore = Parameter("bore", 10)
        bore_x = Parameter("bore_x", 8)
        bore_y = Parameter("bore_y", -5)
        shape = Box(
            60,
            40,
            thickness,
            anchor=Anchor.BOTTOM,
        ) - Cylinder(
            d=bore,
            h=thickness + 20,
        ).at(
            bore_x,
            bore_y,
            0,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "CylinderSubtract",
        )
        self.assertIsInstance(model.root, BooleanSubtractIR)
        self.assertIsInstance(model.root.target, PlacementIR)
        self.assertIsInstance(model.root.target.primitive, BoxIR)
        self.assertIsInstance(model.root.tool, PlacementIR)
        self.assertIsInstance(model.root.tool.primitive, CylinderIR)
        self.assertEqual(model.root.tool.point, (bore_x, bore_y, 0))
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["thickness", "bore", "bore_x", "bore_y"],
        )

        mitcad = compile_mitcad_ir(model, "CylinderSubtract")
        features = [
            row["def"]
            for row in mitcad["commands"]
            if row["cmd"] == "add_feature"
        ]
        self.assertEqual(
            [feature["type"] for feature in features],
            ["box", "cylinder"],
        )
        self.assertEqual(features[0]["operation"], "new_body")
        self.assertEqual(features[1]["operation"], "cut")
        self.assertEqual(features[1]["participants"], [])
        self.assertEqual(features[1]["center"], ["bore_x", "bore_y"])
        self.assertIn("thickness", str(features[1]["height"]))

    def test_circle_extrude_is_one_typed_ir_for_solidcraft_and_mitcad(self):
        diameter = Parameter("diameter", 20)
        height = Parameter("height", 30)
        with Sketch(name="Profile", plane="XY") as sketch:
            Circle2D(d=diameter)
        shape = sketch.extrude(-height)

        model = self.assert_solidcraft_compatibility(
            shape,
            "NegativeCircleExtrude",
        )
        self.assertIsInstance(model.root, CircleExtrudeIR)
        self.assertEqual(model.root.sketch_name, "Profile")
        self.assertEqual(model.root.plane, "XY")
        self.assertEqual(model.root.direction, "negative")

        mitcad = compile_mitcad_ir(model, "NegativeCircleExtrude")
        self.assertEqual(
            [row["cmd"] for row in mitcad["commands"][-2:]],
            ["add_feature", "add_feature"],
        )
        self.assertEqual(
            mitcad["commands"][-1]["def"]["type"],
            "extrude",
        )

    def test_face_boundary_chamfer_keeps_semantic_selector_and_placement(self):
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            2,
            edges=Edges.from_faces(Faces.TOP),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "TopologyFaceBoundaryBox",
        )
        self.assertIsInstance(model.root, ChamferIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertIsInstance(model.root.base.primitive, BoxIR)
        self.assertEqual(model.root.edges.faces, ("top",))

        mitcad = compile_mitcad_ir(model, "TopologyFaceBoundaryBox")
        stage = mitcad["replay"][0]
        self.assertEqual(
            stage["bind_face_boundary_edges"]["face"]["normal"],
            [0, 0, 1],
        )
        self.assertEqual(
            stage["commands"][0]["def"]["type"],
            "chamfer",
        )

    def test_unmigrated_surface_is_explicit_legacy_ir_only_for_solidcraft(self):
        shape = Sphere(10)
        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(model.root.source_kind, "sphere")
        solidcraft = compile_solidcraft_ir(model, "SphereTest")
        self.assertEqual(
            solidcraft["commands"][-1]["command"],
            "solid.sphere",
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'sphere'",
        ):
            compile_mitcad_ir(model, "SphereTest")


if __name__ == "__main__":
    unittest.main()
