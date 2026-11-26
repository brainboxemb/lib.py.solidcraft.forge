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
)
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.compiler import (
    ModelError,
    _compile_shape_legacy_with_dependencies,
)
from scpf.ir import (
    BoxIR,
    ChamferIR,
    CircleExtrudeIR,
    LegacyShapeIR,
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

    def test_parameterized_box_is_typed_once_then_lowered_by_both_backends(self):
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
        self.assertIsInstance(model.root, BoxIR)
        self.assertEqual(model.root.anchor, (0, 0, -1))
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

    def test_face_boundary_chamfer_keeps_semantic_selector_in_ir(self):
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
        shape = Cylinder(d=10, h=20)
        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(model.root.source_kind, "cylinder")
        solidcraft = compile_solidcraft_ir(model, "CylinderTest")
        self.assertEqual(
            solidcraft["commands"][-1]["command"],
            "solid.cylinder",
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'cylinder'",
        ):
            compile_mitcad_ir(model, "CylinderTest")


if __name__ == "__main__":
    unittest.main()
