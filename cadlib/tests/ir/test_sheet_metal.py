from ._support import *

class SheetMetalIRTests(SemanticIRTestCase):
    def test_sheet_metal_history_is_typed_and_solidcraft_compatible(self):
        thickness = Parameter("sheet_thickness", 2)
        bend_radius = Parameter("sheet_radius", 2)
        k_factor = Parameter("sheet_k", 0.5)
        bend_angle = Parameter("sheet_angle", 90)

        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(80, 40)
        sheet = blank.sheet_metal(
            thickness=thickness,
            bend_radius=bend_radius,
            k_factor=k_factor,
            rule_name="Typed Sheet",
        )
        sheet = sheet + Hole(
            d=6,
            direction=(0, 0, -1),
        ).at(-20, 0, thickness)
        shape = sheet.fold(
            line=((20, -20), (20, 20)),
            angle=bend_angle,
            fixed=(-30, 0, 0),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "TypedSheetFold",
        )
        self.assertIsInstance(model.root, SheetFoldIR)
        self.assertIsInstance(model.root.base, HoleIR)
        self.assertIsInstance(model.root.base.target, SheetBaseIR)
        self.assertIsInstance(model.root.base.target.rule, SheetRuleIR)
        self.assertEqual(
            model.parameters,
            (
                ParameterIR("sheet_thickness", 2, roles=("length",)),
                ParameterIR("sheet_radius", 2, roles=("length",)),
                ParameterIR("sheet_k", 0.5, roles=("ratio",)),
                ParameterIR("sheet_angle", 90, roles=("angle",)),
            ),
        )
        with self.assertRaisesRegex(ModelError, "SheetFoldIR"):
            compile_mitcad_ir(model, "TypedSheetFold")

    def test_sheet_feature_family_uses_one_typed_history_contract(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(80, 40)
        base = blank.sheet_metal(
            thickness=2,
            bend_radius=2,
            rule_name="Sheet Rule",
        )

        cases = (
            (
                base.flange(edges=[(40, 0, 2)], height=18, angle=95),
                SheetEdgeFlangeIR,
                "TypedEdgeFlange",
            ),
            (
                base.hem(edges=[(40, 0, 2)], length=12, gap=3),
                SheetHemIR,
                "TypedHem",
            ),
            (
                base.perforate(
                    diameter=4,
                    pitch=8,
                    margin=5,
                    pattern="square",
                ),
                SheetPerforateIR,
                "TypedPerforate",
            ),
        )
        for shape, expected, name in cases:
            with self.subTest(name=name):
                model = self.assert_solidcraft_compatibility(shape, name)
                self.assertIsInstance(model.root, expected)
                self.assertIsInstance(model.root.base, SheetBaseIR)
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(model, name)

    def test_sheet_open_chain_is_semantic_for_contour_path_and_fold(self):
        with Sketch(name="Contour", plane="XZ") as sketch:
            contour = sketch.chain(start=(0, 0))
            contour.line_to((20, 0))
            contour.tangent_arc_to((30, 10))
            contour.line_to((30, 30))
            contour_shape = contour.finish()

        contour_sheet = contour_shape.contour_flange(
            distance=50,
            thickness=2,
            bend_radius=2,
            rule_name="Contour Rule",
        )
        contour_model = self.assert_solidcraft_compatibility(
            contour_sheet,
            "TypedContourSheet",
        )
        self.assertIsInstance(contour_model.root, SheetContourFlangeIR)
        self.assertIsInstance(contour_model.root.contour, SketchChainIR)
        self.assertFalse(contour_model.root.contour.closed)

        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(80, 40)
        base = blank.sheet_metal(thickness=2, bend_radius=2)

        with Sketch(name="Path", plane="XZ") as sketch:
            path = sketch.chain(start=(40, 2))
            path.line_to((40, 14))
            path.line_to((52, 14))
            path_shape = path.finish()
        path_model = self.assert_solidcraft_compatibility(
            base.path_flange(
                edge=(40, 0, 2),
                path=path_shape,
                radius=3,
            ),
            "TypedPathSheet",
        )
        self.assertIsInstance(path_model.root, SheetPathFlangeIR)
        self.assertIsInstance(path_model.root.path, SketchChainIR)

        with Sketch(name="Fold line", plane="XY") as sketch:
            fold_line = sketch.line(
                start=(20, -20),
                end=(20, 20),
            )
        fold_model = self.assert_solidcraft_compatibility(
            base.fold(
                line=fold_line,
                angle=90,
                fixed=(-30, 0, 0),
            ),
            "TypedAssociativeFold",
        )
        self.assertIsInstance(fold_model.root, SheetFoldIR)
        self.assertIsInstance(fold_model.root.line, SketchChainIR)

    def test_connected_profile_sheet_blank_is_typed(self):
        with Sketch(name="MixedBlank", plane="XY") as blank:
            contour = blank.profile(start=(0, 0))
            contour.line_to((40, 0))
            contour.arc_through_to((40, 20), through=(50, 10))
            contour.line_to((0, 20))
            contour.line_to((0, 0))
            contour.close()

        model = self.assert_solidcraft_compatibility(
            blank.sheet_metal(
                thickness=2,
                bend_radius=2,
                rule_name="Mixed Sheet",
            ),
            "TypedConnectedBlank",
        )
        self.assertIsInstance(model.root, SheetBaseIR)
        self.assertIsInstance(model.root.blank, SketchChainIR)
        self.assertTrue(model.root.blank.closed)

    def test_sheet_ir_rejects_invalid_semantic_contracts(self):
        with self.assertRaises(ValueError):
            SheetRuleIR("Bad", 2, 2, 1.0)
        with self.assertRaises(ValueError):
            SheetEdgeFlangeIR(
                base=PlacementIR(
                    primitive=BoxIR(10, 10, 2),
                    point=(0, 0, 0),
                    anchor=(0, 0, 0),
                ),
                edges=((0, 0, 0),),
                height=0,
            )
        with self.assertRaises(ValueError):
            SheetHemIR(
                base=PlacementIR(
                    primitive=BoxIR(10, 10, 2),
                    point=(0, 0, 0),
                    anchor=(0, 0, 0),
                ),
                edges=(),
                length=10,
            )

