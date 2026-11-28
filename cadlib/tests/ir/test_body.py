from ._support import *

class BodyHistoryIRTests(SemanticIRTestCase):
    def test_translated_primitive_remains_absolute_placement_ir(self):
        shape = Box(20, 10, 6).move(x=10, y=-4, z=3)
        model = self.assert_solidcraft_compatibility(
            shape,
            "TranslatedPrimitive",
        )

        self.assertIsInstance(model.root, PlacementIR)
        self.assertEqual(model.root.point, (10, -4, 3))

    def test_translated_primitive_csg_is_semantic_translation_ir(self):
        shape = (
            Box(30, 20, 10)
            - Cylinder(d=6, h=14).move(z=-2)
        ).move(x=10, y=20, z=30)

        model = self.assert_solidcraft_compatibility(
            shape,
            "TranslatedBoolean",
        )

        self.assertIsInstance(model.root, TranslationIR)
        self.assertEqual(model.root.offset, (10, 20, 30))
        self.assertIsInstance(model.root.body, BooleanIR)
        self.assertEqual(model.root.body.operation, "cut")

    def test_translated_union_difference_intersection_keep_source_order(self):
        cases = (
            ("union", Box(20, 20, 10) + Sphere(6)),
            ("difference", Box(20, 20, 10) - Cylinder(d=5, h=14)),
            ("intersection", Box(20, 20, 10) & Sphere(8)),
        )

        for label, body in cases:
            with self.subTest(label=label):
                model = self.assert_solidcraft_compatibility(
                    body.move(x=7, y=-3, z=2),
                    f"Translated{label.title()}",
                )
                self.assertIsInstance(model.root, TranslationIR)
                self.assertIsInstance(model.root.body, BooleanIR)
                self.assertEqual(model.root.offset, (7, -3, 2))

    def test_nested_body_translation_combines_offsets(self):
        body = Box(20, 20, 10) - Cylinder(d=5, h=14)

        model = self.assert_solidcraft_compatibility(
            body.move(x=5, z=2).move(x=7, y=3, z=-1),
            "NestedTranslation",
        )

        self.assertIsInstance(model.root, TranslationIR)
        self.assertEqual(model.root.offset, (12, 3, 1))
        self.assertNotIsInstance(model.root.body, TranslationIR)

    def test_move_of_unsupported_feature_body_remains_visible_legacy_boundary(self):
        with Sketch(name="MovedExtrude", plane="XY") as sketch:
            Rectangle2D(20, 10)
        shape = sketch.extrude(5).move(x=10)

        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "MovedExtrude")

    def test_shell_is_semantic_body_history_with_face_set(self):
        wall = Parameter("wall", 2)
        shape = Box(
            80,
            50,
            30,
            anchor=Anchor.BOTTOM,
        ).shell(
            wall,
            open=(Faces.TOP, Faces.FRONT),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "TypedShell",
        )
        self.assertIsInstance(model.root, BodyIR)
        self.assertIsInstance(model.root, ShellIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertEqual(
            model.root.open_faces,
            FaceSetIR(("top", "front")),
        )
        self.assertIs(model.root.thickness, wall)
        self.assertEqual(
            model.parameters,
            (ParameterIR("wall", 2, roles=("length",)),),
        )

        commands = compile_solidcraft_ir(model, "TypedShell")["commands"]
        self.assertEqual(
            [
                row["command"]
                for row in commands
                if row["command"].startswith(("solid.", "model."))
            ],
            [
                "solid.box",
                "model.faces",
                "model.faces",
                "solid.shell",
            ],
        )
        shell = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.shell"
        )
        self.assertEqual(
            shell["faces"],
            ["$topology_face_name_1", "$topology_face_name_2"],
        )
        self.assertEqual(shell["thickness"], "wall")

        with self.assertRaisesRegex(ModelError, "ShellIR"):
            compile_mitcad_ir(model, "TypedShell")

