"""Contracts for the engine-neutral Forge semantic IR boundary."""
import unittest

from scpf import (
    Anchor,
    Axis,
    AxisLine,
    Boss,
    Box,
    Circle2D,
    Configure,
    Cone,
    CounterboreHole,
    CountersinkHole,
    Cylinder,
    Depth,
    Edges,
    Faces,
    FRONT,
    Hole,
    LEFT,
    Lip,
    Parameter,
    Polygon2D,
    Rectangle2D,
    RoundedRectangle2D,
    Sketch,
    SlotArcCenter2D,
    SlotArcThreePoint2D,
    SlotCenterPoint2D,
    SlotCenterToCenter2D,
    SlotOverall2D,
    Rest,
    SnapFit,
    Sphere,
    Suppress,
    ThreadedHole,
    X,
    Y,
)
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.core import Expression
from scpf.compiler import (
    ModelError,
    _compile_model_with_dependencies,
    _compile_shape_legacy_with_dependencies,
)
from scpf.ir import (
    AxisLineIR,
    BodyIR,
    BossFeatureIR,
    BoundOffsetIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CircularPatternIR,
    ConeIR,
    CylinderIR,
    DirectionPairEdgeSetIR,
    ExplicitEdgePicksIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FaceSetIR,
    FeaturePlacementIR,
    FeatureRefIR,
    FilletIR,
    HoleIR,
    LipFeatureIR,
    PlasticFeatureIR,
    RestFeatureIR,
    SnapFitFeatureIR,
    ConfigurationIR,
    ConfigurationRowIR,
    SuppressionColumnIR,
    LegacyShapeIR,
    ModelIR,
    ParameterIR,
    ParallelEdgeSetIR,
    PlacementIR,
    PlaneIR,
    PolygonProfileIR,
    ProfileEdgeSetIR,
    RegionIR,
    RectangleProfileIR,
    RectangularPatternIR,
    RevolveIR,
    RoundedRectangleProfileIR,
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    SketchIR,
    TextEntityIR,
    TranslationIR,
    SketchCoordinateDimensionIR,
    SketchLengthDimensionIR,
    SketchLineIR,
    SketchOrientationConstraintIR,
    SketchPointIR,
    SketchRelationsIR,
    SketchChainIR,
    SheetBaseIR,
    SheetContourFlangeIR,
    SheetEdgeFlangeIR,
    SheetFoldIR,
    SheetHemIR,
    SheetPathFlangeIR,
    SheetPerforateIR,
    SheetRuleIR,
    ShellIR,
    SlotProfileIR,
    SphereIR,
    normalize_model,
    normalize_shape,
    resolve_feature_ref,
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
        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "cut")
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

    def test_sphere_and_primitive_csg_use_recursive_typed_ir(self):
        sphere = self.assert_solidcraft_compatibility(
            Sphere(20),
            "SphereTest",
        )
        self.assertIsInstance(sphere.root, PlacementIR)
        self.assertIsInstance(sphere.root.primitive, SphereIR)
        self.assertEqual(sphere.root.primitive.radius, 20)
        self.assertEqual(sphere.root.anchor, (0, 0, 0))

        shape = Sphere(20)
        shape = shape + Box(30, 30, 20).move(x=18, z=10)
        shape = shape - Cylinder(d=8, h=60, axis=Axis.X)
        shape = shape & Box(50, 50, 30).move(z=15)

        model = self.assert_solidcraft_compatibility(shape, "PrimitiveCsg")
        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "intersect")
        self.assertIsInstance(model.root.tool, PlacementIR)
        self.assertIsInstance(model.root.tool.primitive, BoxIR)

        cut = model.root.target
        self.assertIsInstance(cut, BooleanIR)
        self.assertEqual(cut.operation, "cut")
        self.assertIsInstance(cut.tool.primitive, CylinderIR)

        join = cut.target
        self.assertIsInstance(join, BooleanIR)
        self.assertEqual(join.operation, "join")
        self.assertIsInstance(join.target, PlacementIR)
        self.assertIsInstance(join.target.primitive, SphereIR)
        self.assertIsInstance(join.tool.primitive, BoxIR)

        mitcad = compile_mitcad_ir(model, "PrimitiveCsg")
        features = [
            row["def"]
            for row in mitcad["commands"]
            if row["cmd"] == "add_feature"
        ]
        self.assertEqual(
            [feature["type"] for feature in features],
            ["sphere", "box", "cylinder", "box"],
        )
        self.assertEqual(
            [feature["operation"] for feature in features],
            ["new_body", "join", "cut", "intersect"],
        )
        self.assertEqual(features[0]["diameter"], 40)
        self.assertEqual(features[0]["center"], [0, 0])
        self.assertFalse(features[1]["symmetric"])
        self.assertFalse(features[3]["symmetric"])
        self.assertEqual(features[1]["corner"], [3.0, -15.0])
        self.assertEqual(features[3]["corner"], [-25.0, -25.0])

    def test_sphere_placement_reuses_generic_placement_ir(self):
        anchored = Sphere(20, anchor=Anchor.TOP)
        anchored_model = self.assert_solidcraft_compatibility(
            anchored,
            "AnchoredSphere",
        )
        self.assertIsInstance(anchored_model.root, PlacementIR)
        self.assertIsInstance(anchored_model.root.primitive, SphereIR)
        self.assertEqual(anchored_model.root.point, (0, 0, 0))
        self.assertEqual(anchored_model.root.anchor, (0, 0, 1))

        anchored_mitcad = compile_mitcad_ir(
            anchored_model,
            "AnchoredSphere",
        )
        anchored_plane = anchored_mitcad["commands"][-2]
        anchored_sphere = anchored_mitcad["commands"][-1]
        self.assertEqual(
            anchored_plane["def"],
            {
                "type": "construction_plane",
                "definition": {
                    "type": "offset",
                    "plane": "xy",
                    "distance": -20,
                },
            },
        )
        self.assertEqual(anchored_sphere["def"]["plane"], {"ref": "sphere_plane.uid"})
        self.assertEqual(anchored_sphere["def"]["center"], [0, 0])
        self.assertEqual(anchored_sphere["def"]["diameter"], 40)

        moved = Sphere(20).move(z=10)
        moved_model = self.assert_solidcraft_compatibility(
            moved,
            "MovedSphere",
        )
        self.assertIsInstance(moved_model.root, PlacementIR)
        self.assertEqual(moved_model.root.point, (0, 0, 10))
        self.assertEqual(moved_model.root.anchor, (0, 0, 0))
        moved_mitcad = compile_mitcad_ir(moved_model, "MovedSphere")
        self.assertEqual(
            moved_mitcad["commands"][-2]["def"]["definition"]["distance"],
            10,
        )

    def test_parameterized_sphere_anchor_keeps_world_point_dependencies(self):
        radius = Parameter("sphere_radius", 10)
        sphere_z = Parameter("sphere_z", 25)
        shape = Sphere(radius).at(
            3,
            4,
            sphere_z,
            anchor=Anchor.TOP,
        )
        model = self.assert_solidcraft_compatibility(
            shape,
            "ParameterizedSphere",
        )
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIs(model.root.primitive.radius, radius)
        self.assertEqual(model.root.point[:2], (3, 4))
        self.assertIs(model.root.point[2], sphere_z)
        self.assertEqual(model.root.anchor, (0, 0, 1))

        mitcad = compile_mitcad_ir(model, "ParameterizedSphere")
        plane = next(
            row
            for row in mitcad["commands"]
            if row.get("def", {}).get("type") == "construction_plane"
        )
        sphere = mitcad["commands"][-1]
        distance = str(plane["def"]["definition"]["distance"])
        self.assertIn("sphere_z", distance)
        self.assertIn("sphere_radius", distance)
        self.assertEqual(sphere["def"]["plane"], {"ref": "sphere_plane.uid"})
        self.assertEqual(sphere["def"]["center"], [3, 4])
        self.assertIn("sphere_radius", str(sphere["def"]["diameter"]))

    def test_shifted_or_anchored_sphere_csg_keeps_typed_boolean_ir(self):
        for index, sphere in enumerate(
            (
                Sphere(20, anchor=Anchor.TOP),
                Sphere(20).move(z=10),
            ),
            start=1,
        ):
            with self.subTest(sphere=sphere):
                shape = sphere + Box(10, 10, 10)
                model = self.assert_solidcraft_compatibility(
                    shape,
                    f"SphereCsg{index}",
                )
                self.assertIsInstance(model.root, BooleanIR)
                self.assertIsInstance(model.root.target, PlacementIR)
                self.assertIsInstance(model.root.target.primitive, SphereIR)

                mitcad = compile_mitcad_ir(model, f"SphereCsg{index}")
                features = [
                    row
                    for row in mitcad["commands"]
                    if row["cmd"] == "add_feature"
                ]
                self.assertEqual(
                    [row["def"]["type"] for row in features],
                    ["construction_plane", "sphere", "box"],
                )
                self.assertEqual(features[1]["def"]["operation"], "new_body")
                self.assertEqual(features[2]["def"]["operation"], "join")
                self.assertTrue(
                    features[0]["as"].startswith("csg_plane_root_target")
                )
                self.assertEqual(
                    features[1]["def"]["plane"],
                    {"ref": f"{features[0]['as']}.uid"},
                )

    def test_shifted_sphere_configuration_binds_semantic_feature_not_helper(self):
        sphere = Sphere(5).move(z=15)
        body = Box(30, 30, 30, anchor=Anchor.BOTTOM) - sphere
        configured = Configure(
            body,
            active="Cut",
            columns=(Suppress(sphere),),
            rows={
                "Cut": (False,),
                "Uncut": (True,),
            },
        )

        model = normalize_model(configured)
        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(
            model.configuration.columns[0].feature,
            FeatureRefIR(path=("root", "tool")),
        )

        mitcad = compile_mitcad_ir(model, "ShiftedSphereConfigured")
        helper = next(
            row
            for row in mitcad["commands"]
            if row.get("as") == "csg_plane_root_tool"
        )
        self.assertEqual(helper["def"]["type"], "construction_plane")
        configured_feature = next(
            row
            for row in mitcad["commands"]
            if row.get("as") == "configured_feature"
        )
        self.assertEqual(configured_feature["def"]["type"], "sphere")
        self.assertEqual(configured_feature["def"]["operation"], "cut")
        self.assertNotEqual(helper, configured_feature)

    def test_offset_cone_csg_reuses_boolean_ir_and_backend_lowering(self):
        cone = Cone(
            d=10,
            top_d=0,
            h=20,
            anchor=Anchor.BOTTOM,
        ).at(
            0,
            0,
            5,
            anchor=Anchor.BOTTOM,
        )
        shape = Box(30, 30, 30, anchor=Anchor.BOTTOM) - cone

        model = self.assert_solidcraft_compatibility(
            shape,
            "OffsetConeCut",
        )
        self.assertIsInstance(model.root, BooleanIR)
        self.assertIsInstance(model.root.tool, PlacementIR)
        self.assertIsInstance(model.root.tool.primitive, ConeIR)
        self.assertEqual(model.root.tool.point, (0, 0, 5))
        self.assertEqual(model.root.tool.anchor, (0, 0, -1))

        solidcraft = compile_solidcraft_ir(model, "OffsetConeCut")
        geometry = [
            row
            for row in solidcraft["commands"]
            if row["command"] in {"solid.box", "solid.cone"}
        ]
        self.assertEqual(
            [row["command"] for row in geometry],
            ["solid.box", "solid.cone"],
        )
        self.assertEqual(geometry[0]["params"]["operation"], "new")
        self.assertEqual(geometry[1]["params"]["operation"], "cut")
        self.assertEqual(geometry[1]["params"]["base"], [0, 0, 5])
        self.assertEqual(geometry[1]["params"]["targets"], ["OffsetConeCut"])

        mitcad = compile_mitcad_ir(model, "OffsetConeCut")
        features = [
            row
            for row in mitcad["commands"]
            if row["cmd"] == "add_feature"
        ]
        self.assertEqual(
            [row["def"]["type"] for row in features],
            ["box", "construction_plane", "cone"],
        )
        self.assertEqual(features[1]["as"], "csg_plane_root_tool")
        self.assertEqual(
            features[1]["def"]["definition"]["distance"],
            5,
        )
        self.assertEqual(
            features[2]["def"]["plane"],
            {"ref": "csg_plane_root_tool.uid"},
        )
        self.assertEqual(features[2]["def"]["operation"], "cut")

    def test_offset_cone_configuration_binds_feature_not_helper(self):
        cone = Cone(
            d=10,
            top_d=0,
            h=20,
            anchor=Anchor.BOTTOM,
        ).at(
            0,
            0,
            5,
            anchor=Anchor.BOTTOM,
        )
        body = Box(30, 30, 30, anchor=Anchor.BOTTOM) - cone
        configured = Configure(
            body,
            active="Cut",
            columns=(Suppress(cone),),
            rows={
                "Cut": (False,),
                "Uncut": (True,),
            },
        )

        model = normalize_model(configured)
        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(
            model.configuration.columns[0].feature,
            FeatureRefIR(path=("root", "tool")),
        )

        mitcad = compile_mitcad_ir(model, "ConfiguredConeCut")
        helper = next(
            row
            for row in mitcad["commands"]
            if row.get("as") == "csg_plane_root_tool"
        )
        self.assertEqual(helper["def"]["type"], "construction_plane")
        configured_feature = next(
            row
            for row in mitcad["commands"]
            if row.get("as") == "configured_feature"
        )
        self.assertEqual(configured_feature["def"]["type"], "cone")
        self.assertEqual(configured_feature["def"]["operation"], "cut")
        self.assertNotEqual(helper, configured_feature)

    def test_cone_boolean_join_uses_existing_operation_semantics(self):
        cone = Cone(
            d=8,
            top_d=2,
            h=10,
            anchor=Anchor.BOTTOM,
        )
        shape = Box(20, 20, 10, anchor=Anchor.BOTTOM) + cone

        model = self.assert_solidcraft_compatibility(
            shape,
            "ConeJoin",
        )
        self.assertIsInstance(model.root, BooleanIR)
        self.assertIsInstance(model.root.tool.primitive, ConeIR)

        solidcraft = compile_solidcraft_ir(model, "ConeJoin")
        cone_command = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.cone"
        )
        self.assertEqual(cone_command["params"]["operation"], "join")

        mitcad = compile_mitcad_ir(model, "ConeJoin")
        cone_feature = next(
            row
            for row in mitcad["commands"]
            if row.get("def", {}).get("type") == "cone"
        )
        self.assertEqual(cone_feature["def"]["operation"], "join")

    def test_revolve_complete_direct_profile_grammar_is_typed(self):
        cases = (
            ("circle", lambda: Circle2D(d=8), CircleProfileIR),
            ("rectangle", lambda: Rectangle2D(8, 4), RectangleProfileIR),
            (
                "rounded_rectangle",
                lambda: RoundedRectangle2D(10, 6, 1),
                RoundedRectangleProfileIR,
            ),
            (
                "polygon",
                lambda: Polygon2D(
                    [(0, 0), (0, 4), (8, 4), (8, 0)],
                    plane="XZ",
                ),
                PolygonProfileIR,
            ),
        )

        for label, factory, profile_type in cases:
            with self.subTest(label=label):
                with Sketch(name=f"{label}Profile", plane="XZ") as sketch:
                    factory()
                shape = sketch.revolve(axis=Axis.X, angle=180)
                model = self.assert_solidcraft_compatibility(
                    shape,
                    f"{label.title().replace('_', '')}Revolve",
                )
                self.assertIsInstance(model.root, RevolveIR)
                self.assertIsInstance(
                    model.root.sketch.profiles[0],
                    profile_type,
                )
                self.assertEqual(model.root.region, RegionIR(outer=0))

    def test_revolve_connected_profile_uses_completed_sketch_graph(self):
        with Sketch(name="ConnectedRevolve", plane="XZ") as sketch:
            profile = sketch.profile(start=(2, 0))
            profile.line_to((2, 6))
            profile.arc_through_to((8, 0), through=(8, 6))
            profile.line_to((2, 0))
            profile.close()

        shape = sketch.revolve(axis=Axis.X, angle=120)
        model = self.assert_solidcraft_compatibility(
            shape,
            "ConnectedProfileRevolve",
        )

        self.assertIsInstance(model.root, RevolveIR)
        self.assertIsNone(model.root.region)
        self.assertIsInstance(
            model.root.sketch.graph.entities[0],
            SketchChainIR,
        )

    def test_revolve_symmetric_sweep_is_typed(self):
        with Sketch(name="SymmetricRevolve", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 4), (8, 4), (8, 0)],
                plane="XZ",
            )

        shape = sketch.revolve(axis=Axis.X, angle=140, sym=True)
        model = self.assert_solidcraft_compatibility(
            shape,
            "SymmetricRevolve",
        )

        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(model.root.direction, "symmetric")
        solidcraft = compile_solidcraft_ir(model, "SymmetricRevolve")
        revolve = solidcraft["commands"][-1]
        self.assertEqual(revolve["command"], "solid.revolve")
        self.assertEqual(revolve["params"]["direction"], "symmetric")
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "SymmetricRevolve")

    def test_revolve_does_not_type_unsupported_standalone_sketch_forms(self):
        unsupported = []

        with Sketch(name="SlotRevolve", plane="XZ") as sketch:
            SlotCenterToCenter2D((2, 0), (10, 0), 4)
        unsupported.append(sketch.revolve(axis=Axis.X, angle=90))

        with Sketch(name="TextRevolve", plane="XZ") as sketch:
            from scpf.core import Text2D
            Text2D("A", height=5)
        unsupported.append(sketch.revolve(axis=Axis.X, angle=90))

        with Sketch(name="PatternRevolve", plane="XZ") as sketch:
            source = Circle2D(d=4)
            sketch.rectangular_pattern(
                source,
                count=2,
                spacing=8,
                direction=Axis.X,
            )
        unsupported.append(sketch.revolve(axis=Axis.X, angle=90))

        for shape in unsupported:
            with self.subTest(kind=shape.kind):
                self.assertIsInstance(normalize_shape(shape).root, LegacyShapeIR)

    def test_revolve_symbolic_non_affine_angle_keeps_typed_scalar_semantics(self):
        sweep = Parameter("sweep", 30)
        radius = Parameter("radius", 4)
        with Sketch(name="SymbolicRevolve", plane="XZ") as sketch:
            Rectangle2D(radius * 2, 5)

        shape = sketch.revolve(
            axis=Axis.X,
            angle=(sweep ** 2) / 30,
        )
        model = self.assert_solidcraft_compatibility(
            shape,
            "SymbolicRevolve",
        )

        self.assertIsInstance(model.root, RevolveIR)
        self.assertIsNotNone(model.root.angle.scalar_ir)
        self.assertEqual(
            {parameter.name for parameter in model.parameters},
            {"sweep", "radius"},
        )

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

    def test_center_alignment_preserves_symbolic_primitive_delta(self):
        target_width = Parameter("target_width", 40)
        target = Box(
            target_width,
            20,
            10,
            anchor=Anchor.LEFT,
        )
        shape = Box(10, 10, 10).at(target)

        model = self.assert_solidcraft_compatibility(
            shape,
            "SymbolicCenterAlignment",
        )

        self.assertIsInstance(model.root, PlacementIR)
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["target_width"],
        )
        self.assertEqual(model.root.point[0].scalar_ir.operation, "divide")

    def test_move_of_unsupported_feature_body_remains_visible_legacy_boundary(self):
        with Sketch(name="MovedExtrude", plane="XY") as sketch:
            Rectangle2D(20, 10)
        shape = sketch.extrude(5).move(x=10)

        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "MovedExtrude")

    def test_translation_feature_ref_descends_into_boolean_body_semantics(self):
        base = Box(30, 20, 10)
        bore = Cylinder(d=6, h=14)
        design = (base - bore).move(x=10)
        configured = Configure(
            design,
            active="Cut",
            columns=(Suppress(bore),),
            rows={"Cut": (False,), "Keep": (True,)},
        )

        model = normalize_model(configured)

        self.assertIsInstance(model.root, TranslationIR)
        reference = model.configuration.columns[0].feature
        self.assertEqual(
            reference,
            FeatureRefIR(path=("root", "body", "tool")),
        )
        resolved = resolve_feature_ref(model.root, reference)
        self.assertIsInstance(resolved, PlacementIR)
        self.assertIsInstance(resolved.primitive, CylinderIR)


    def test_boolean_ir_composes_typed_extrude_target_with_primitive_tool(self):
        with Sketch(name="BooleanBase", plane="XY") as base_profile:
            Rectangle2D(30, 20)
        base = base_profile.extrude(8)
        bore = Cylinder(d=6, h=20, axis=Axis.Z)

        shape = base - bore
        model = self.assert_solidcraft_compatibility(
            shape,
            "ExtrudeBooleanTarget",
        )

        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "cut")
        self.assertIsInstance(model.root.target, ExtrudeIR)
        self.assertIsInstance(model.root.tool, PlacementIR)

    def test_boolean_ir_composes_standalone_extrude_as_typed_tool(self):
        base = Box(40, 30, 10)
        with Sketch(name="JoinProfile", plane="XY") as tool_profile:
            Circle2D(d=12)
        tool = tool_profile.extrude(14)

        shape = base + tool
        model = self.assert_solidcraft_compatibility(
            shape,
            "ExtrudeBooleanTool",
        )

        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "join")
        self.assertIsInstance(model.root.target, PlacementIR)
        self.assertIsInstance(model.root.tool, ExtrudeIR)
        solidcraft = compile_solidcraft_ir(model, "ExtrudeBooleanTool")
        extrude = [
            command
            for command in solidcraft["commands"]
            if command["command"] == "solid.extrude"
        ][-1]
        self.assertEqual(extrude["params"]["operation"], "join")
        self.assertEqual(extrude["params"]["targets"], ["ExtrudeBooleanTool"])
        with self.assertRaisesRegex(
            ModelError,
            "unsupported typed tool ExtrudeIR",
        ):
            compile_mitcad_ir(model, "ExtrudeBooleanTool")

    def test_boolean_ir_composes_standalone_revolve_as_typed_tool(self):
        base = Box(40, 30, 10)
        with Sketch(name="JoinRevolve", plane="XZ") as tool_profile:
            Polygon2D([(0, 0), (0, 4), (8, 4), (8, 0)], plane="XZ")
        tool = tool_profile.revolve(axis=Axis.X, angle=180)

        shape = base | tool
        model = self.assert_solidcraft_compatibility(
            shape,
            "RevolveBooleanTool",
        )

        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "join")
        self.assertIsInstance(model.root.tool, RevolveIR)
        solidcraft = compile_solidcraft_ir(model, "RevolveBooleanTool")
        revolve = [
            command
            for command in solidcraft["commands"]
            if command["command"] == "solid.revolve"
        ][-1]
        self.assertEqual(revolve["params"]["operation"], "join")
        self.assertEqual(revolve["params"]["targets"], ["RevolveBooleanTool"])

    def test_boolean_ir_preserves_recursive_target_and_tool_order(self):
        with Sketch(name="TargetProfile", plane="XY") as target_profile:
            Rectangle2D(24, 16)
        target = target_profile.extrude(6)
        first_tool = Cylinder(d=5, h=12)
        left = target - first_tool

        with Sketch(name="ToolProfile", plane="XY") as tool_profile:
            Circle2D(d=10)
        right = tool_profile.extrude(8)

        model = normalize_shape(left & right)

        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "intersect")
        self.assertIsInstance(model.root.target, BooleanIR)
        self.assertEqual(model.root.target.operation, "cut")
        self.assertIsInstance(model.root.target.target, ExtrudeIR)
        self.assertIsInstance(model.root.target.tool, PlacementIR)
        self.assertIsInstance(model.root.tool, ExtrudeIR)
        self.assertNotIsInstance(model.root, LegacyShapeIR)

    def test_boolean_feature_ref_recurses_through_typed_tool_history(self):
        base = Box(30, 30, 10)
        first = Cylinder(d=6, h=12)
        second = Cylinder(d=4, h=12).move(x=8)
        tool = first + second
        design = base - tool

        configured = Configure(
            design,
            active="Cut",
            columns=(Suppress(second),),
            rows={"Cut": (False,), "Keep": (True,)},
        )
        model = normalize_model(configured)

        self.assertIsInstance(model.root, BooleanIR)
        reference = model.configuration.columns[0].feature
        self.assertEqual(
            reference,
            FeatureRefIR(path=("root", "tool", "tool")),
        )
        resolved = resolve_feature_ref(model.root, reference)
        self.assertIsInstance(resolved, PlacementIR)
        self.assertIsInstance(resolved.primitive, CylinderIR)


    def test_boolean_ir_rejects_non_body_operands_at_node_boundary(self):
        placed = normalize_shape(Box(10, 10, 10)).root
        legacy = LegacyShapeIR(
            shape=Box(2, 2, 2).with_appearance("#112233"),
            source_kind="appearance_assignment",
        )

        with self.assertRaisesRegex(ValueError, "tool must be typed BodyIR"):
            BooleanIR(operation="join", target=placed, tool=legacy)

    def test_material_appearance_assignment_remains_invalid_csg_operand(self):
        assigned = Box(10, 10, 10).with_appearance("#112233")

        with self.assertRaisesRegex(TypeError, "cannot be combined"):
            _ = assigned + Box(2, 2, 2)


    def test_rectangle_and_rounded_rectangle_profiles_are_semantic(self):
        width = Parameter("rect_width", 40)
        depth = Parameter("rect_depth", 20)
        offset_x = Parameter("rect_x", 7)
        with Sketch(name="Rectangle", plane="XY") as sketch:
            rectangle = Rectangle2D(width, depth)
            sketch.add(rectangle, offset=(offset_x, 3))
        shape = sketch.extrude(8, sym=True)

        model = self.assert_solidcraft_compatibility(
            shape,
            "TypedRectangle",
        )
        self.assertIsInstance(model.root, ExtrudeIR)
        profile = model.root.sketch.profiles[0]
        self.assertIsInstance(profile, RectangleProfileIR)
        self.assertIs(profile.width, width)
        self.assertIs(profile.depth, depth)
        self.assertEqual(profile.center, (offset_x, 3))
        self.assertEqual(model.root.direction, "symmetric")
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "TypedRectangle")

        radius = Parameter("corner_radius", 4)
        with Sketch(name="Rounded", plane="XZ") as rounded:
            RoundedRectangle2D(50, 24, radius)
        rounded_shape = rounded.extrude(-6)
        rounded_model = self.assert_solidcraft_compatibility(
            rounded_shape,
            "TypedRounded",
        )
        rounded_profile = rounded_model.root.sketch.profiles[0]
        self.assertIsInstance(
            rounded_profile,
            RoundedRectangleProfileIR,
        )
        self.assertIs(rounded_profile.radius, radius)
        self.assertEqual(rounded_model.root.direction, "negative")

    def test_slot_profile_family_is_semantic(self):
        cases = (
            (
                "center_to_center",
                lambda: SlotCenterToCenter2D((-12, 0), (12, 0), 6),
            ),
            (
                "overall",
                lambda: SlotOverall2D((-15, 0), (15, 0), 6),
            ),
            (
                "center_point",
                lambda: SlotCenterPoint2D((0, 0), (12, 0), 6),
            ),
            (
                "arc_three_point",
                lambda: SlotArcThreePoint2D(
                    (-12, 0),
                    (0, 8),
                    (12, 0),
                    6,
                ),
            ),
            (
                "arc_center_sweep",
                lambda: SlotArcCenter2D(
                    (0, 0),
                    (12, 0),
                    6,
                    sweep=120,
                ),
            ),
            (
                "arc_center_end",
                lambda: SlotArcCenter2D(
                    (0, 0),
                    (12, 0),
                    6,
                    end=(0, 12),
                ),
            ),
        )
        for index, (construction, factory) in enumerate(cases, start=1):
            with self.subTest(construction=construction):
                with Sketch(name=f"Slot{index}", plane="XY") as sketch:
                    factory()
                shape = sketch.extrude(5)
                model = normalize_shape(shape)
                self.assertIsInstance(model.root, ExtrudeIR)
                profile = model.root.sketch.profiles[0]
                self.assertIsInstance(profile, SlotProfileIR)
                self.assertEqual(profile.construction, construction)

                commands = compile_solidcraft_ir(
                    model,
                    f"TypedSlot{index}",
                )["commands"]
                expected_command = {
                    "center_to_center": "sketch.slot.center_to_center",
                    "overall": "sketch.slot.overall",
                    "center_point": "sketch.slot.center_point",
                    "arc_three_point": "sketch.slot.arc_three_point",
                    "arc_center_sweep": "sketch.slot.arc_center",
                    "arc_center_end": "sketch.slot.arc_center",
                }[construction]
                self.assertIn(
                    expected_command,
                    [row["command"] for row in commands],
                )
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(model, f"TypedSlot{index}")

    def test_basic_closed_profiles_support_all_finite_extrude_directions(self):
        factories = (
            ("circle", lambda: Circle2D(d=10)),
            (
                "polygon",
                lambda: Polygon2D(
                    [(-8, -5), (8, -5), (8, 5), (-8, 5)],
                    plane="XY",
                ),
            ),
            ("rectangle", lambda: Rectangle2D(20, 12)),
            (
                "rounded_rectangle",
                lambda: RoundedRectangle2D(20, 12, 2),
            ),
            (
                "slot_center_to_center",
                lambda: SlotCenterToCenter2D((-8, 0), (8, 0), 4),
            ),
            (
                "slot_overall",
                lambda: SlotOverall2D((-10, 0), (10, 0), 4),
            ),
            (
                "slot_center_point",
                lambda: SlotCenterPoint2D((0, 0), (8, 0), 4),
            ),
            (
                "slot_arc_three_point",
                lambda: SlotArcThreePoint2D(
                    (-8, 0), (0, 6), (8, 0), 4
                ),
            ),
            (
                "slot_arc_center",
                lambda: SlotArcCenter2D(
                    (0, 0), (8, 0), 4, sweep=120
                ),
            ),
        )
        directions = (
            ("positive", 5, False),
            ("negative", -5, False),
            ("symmetric", 5, True),
        )
        for profile_name, factory in factories:
            for direction, distance, symmetric in directions:
                with self.subTest(
                    profile=profile_name,
                    direction=direction,
                ):
                    with Sketch(
                        name=f"{profile_name}_{direction}",
                        plane="XY",
                    ) as sketch:
                        factory()
                    shape = sketch.extrude(
                        distance,
                        sym=symmetric,
                    )
                    model = normalize_shape(shape)
                    self.assertIsInstance(model.root, ExtrudeIR)
                    self.assertEqual(model.root.direction, direction)
                    compile_solidcraft_ir(
                        model,
                        f"{profile_name}_{direction}",
                    )

    def test_parameterized_straight_slot_keeps_semantic_dimensions(self):
        length = Parameter("slot_length", 30)
        width = Parameter("slot_width", 8)
        x = Parameter("slot_x", 5)
        with Sketch(name="ParametricSlot", plane="XY") as sketch:
            slot = SlotCenterToCenter2D(
                (-length / 2, 0),
                (length / 2, 0),
                width,
            )
            sketch.add(slot, offset=(x, 4))
        shape = sketch.extrude(6)

        model = normalize_shape(shape)
        self.assertIsInstance(model.root, ExtrudeIR)
        profile = model.root.sketch.profiles[0]
        self.assertIsInstance(profile, SlotProfileIR)
        self.assertEqual(profile.offset, (x, 4))
        self.assertIs(profile.width, width)

        commands = compile_solidcraft_ir(
            model,
            "ParametricSlot",
        )["commands"]
        names = [row["command"] for row in commands]
        self.assertIn("sketch.draw.dimensioned", names)
        self.assertIn("sketch.constraint.horizontal_vertical", names)
        self.assertEqual(names.count("sketch.dimension"), 2)

    def test_circle_and_polygon_profile_offsets_remain_semantic(self):
        circle_x = Parameter("circle_x", 9)
        with Sketch(name="OffsetCircle", plane="XY") as sketch:
            circle = Circle2D(d=10)
            sketch.add(circle, offset=(circle_x, -3))
        circle_shape = sketch.extrude(4)
        circle_model = self.assert_solidcraft_compatibility(
            circle_shape,
            "OffsetCircle",
        )
        circle_profile = circle_model.root.sketch.profiles[0]
        self.assertIsInstance(circle_profile, CircleProfileIR)
        self.assertEqual(circle_profile.center, (circle_x, -3))

        polygon_x = Parameter("polygon_x", 6)
        with Sketch(name="OffsetPolygon", plane="XY") as polygon_sketch:
            polygon = Polygon2D(
                [(-10, -5), (10, -5), (10, 5), (-10, 5)],
                plane="XY",
            )
            polygon_sketch.add(polygon, offset=(polygon_x, 2))
        polygon_shape = polygon_sketch.extrude(4)
        polygon_model = normalize_shape(polygon_shape)
        self.assertIsInstance(polygon_model.root, ExtrudeIR)
        polygon_commands = compile_solidcraft_ir(
            polygon_model,
            "OffsetPolygon",
        )["commands"]
        self.assertIn(
            "sketch.line",
            [row["command"] for row in polygon_commands],
        )
        polygon_profile = polygon_model.root.sketch.profiles[0]
        self.assertIsInstance(polygon_profile, PolygonProfileIR)
        self.assertIn("polygon_x", str(polygon_profile.points[0][0]))

    def test_absolute_plastic_feature_family_is_typed_history(self):
        size = Parameter("plastic_size", 4)
        body = Box(100, 60, 12, anchor=Anchor.BOTTOM)
        features = (
            Lip(width=size, height=3).at(-30, 0, 12),
            SnapFit(
                length=20,
                thickness=2,
                width=8,
                catch_depth=1.5,
                catch_length=4,
                hook=(1, 0, 0),
                direction=(0, 0, 1),
            ).at(-10, 0, 12),
            Boss(
                d=10,
                h=8,
                hole_d=3,
                direction=(0, 0, 1),
            ).at(10, 0, 12),
            Rest(
                width=12,
                height=size,
                length=24,
                along=(1, 0, 0),
                direction=(0, 0, 1),
            ).at(30, 0, 12),
        )
        for feature in features:
            body = body + feature

        model = self.assert_solidcraft_compatibility(
            body,
            "TypedPlasticFamily",
        )
        self.assertIsInstance(model.root, PlasticFeatureIR)

        nodes = []
        current = model.root
        while isinstance(current, PlasticFeatureIR):
            nodes.append(current)
            current = current.target
        nodes.reverse()

        self.assertEqual(len(nodes), 4)
        self.assertIsInstance(current, PlacementIR)
        self.assertEqual(
            [type(node.feature) for node in nodes],
            [
                LipFeatureIR,
                SnapFitFeatureIR,
                BossFeatureIR,
                RestFeatureIR,
            ],
        )
        self.assertTrue(
            all(
                isinstance(node.placement, FeaturePlacementIR)
                and node.placement.mode == "absolute"
                for node in nodes
            )
        )
        self.assertEqual(
            model.parameters,
            (ParameterIR("plastic_size", 4, roles=("length",)),),
        )

        commands = compile_solidcraft_ir(
            model,
            "TypedPlasticFamily",
        )["commands"]
        self.assertEqual(
            [
                row["command"]
                for row in commands
                if row["command"].startswith("plastic.")
            ],
            [
                "plastic.lip",
                "plastic.snap_fit",
                "plastic.boss",
                "plastic.rest",
            ],
        )
        with self.assertRaisesRegex(ModelError, "PlasticFeatureIR"):
            compile_mitcad_ir(model, "TypedPlasticFamily")

    def test_anchored_plastic_placement_preserves_bounds_and_shell_intent(self):
        delta = Parameter("lip_delta", 2)
        wall = Parameter("wall", 2)
        shell = Box(
            80,
            50,
            30,
            anchor=Anchor.BOTTOM,
        ).shell(
            wall,
            open=Faces.TOP,
        )
        lip = Lip(width=3, height=4).attach(
            shell,
            parent=Anchor.INNER_BOTTOM,
            child=Anchor.BOTTOM,
            offset=(X.MIN + 10 + delta, Y.MAX - 5),
        )
        shape = shell + lip

        model = self.assert_solidcraft_compatibility(
            shape,
            "AnchoredLip",
        )
        self.assertIsInstance(model.root, PlasticFeatureIR)
        placement = model.root.placement
        self.assertEqual(placement.mode, "anchored")
        self.assertEqual(placement.parent_anchor, "inner_bottom")
        self.assertEqual(placement.child_anchor, "bottom")
        self.assertIsInstance(placement.offset[0], BoundOffsetIR)
        self.assertIsInstance(placement.offset[1], BoundOffsetIR)
        self.assertEqual(placement.offset[0].axis, "X")
        self.assertEqual(placement.offset[0].reference, "min")
        self.assertEqual(placement.offset[1].axis, "Y")
        self.assertEqual(placement.offset[1].reference, "max")
        self.assertIn("lip_delta", str(placement.offset[0].delta))
        self.assertEqual(
            model.parameters,
            (
                ParameterIR("wall", 2, roles=("length",)),
                ParameterIR("lip_delta", 2, roles=("length",)),
            ),
        )

        plastic = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "AnchoredLip",
            )["commands"]
            if row["command"] == "plastic.lip"
        )
        self.assertEqual(plastic["body"], "AnchoredLip")
        self.assertEqual(plastic["face"][2], 2.0)

    def test_anchored_hole_uses_generic_feature_placement(self):
        x = Parameter("hole_x", 7)
        diameter = Parameter("bore_d", 6)
        plate = Box(
            60,
            40,
            10,
            anchor=Anchor.BOTTOM,
        )
        hole = Hole(
            d=diameter,
            depth=Depth.THROUGH_ALL,
        ).attach(
            plate,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
            offset=(x, 0),
        )
        shape = plate + hole

        model = self.assert_solidcraft_compatibility(
            shape,
            "AnchoredHole",
        )
        self.assertIsInstance(model.root, HoleIR)
        self.assertIsInstance(model.root.placement, FeaturePlacementIR)
        self.assertEqual(model.root.placement.mode, "anchored")
        self.assertEqual(model.root.placement.parent_anchor, "top")
        self.assertEqual(model.root.placement.child_anchor, "bottom")
        self.assertEqual(model.root.placement.offset, (x, 0))
        self.assertIsNone(model.root.point)

        commands = compile_solidcraft_ir(
            model,
            "AnchoredHole",
        )["commands"]
        self.assertEqual(
            [
                row["command"]
                for row in commands
                if row["command"].startswith(("sketch.", "solid."))
            ],
            [
                "solid.box",
                "sketch.create",
                "sketch.circle.center",
                "sketch.finish",
                "solid.extrude",
            ],
        )
        circle = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.circle.center"
        )
        self.assertEqual(circle["center"], ["(hole_x)", 0.0])
        cut = commands[-1]["params"]
        self.assertEqual(cut["direction"], "positive")
        self.assertEqual(cut["distance"], 10)
        self.assertEqual(cut["name"], "Hole")
        with self.assertRaisesRegex(ModelError, "HoleIR"):
            compile_mitcad_ir(model, "AnchoredHole")

    def test_bottom_face_hole_uses_typed_anchored_placement(self):
        plate = Box(40, 30, 10, anchor=Anchor.BOTTOM)
        shape = plate + Hole(
            d=4,
            depth=3,
        ).on(
            plate,
            face=Faces.BOTTOM,
            offset=(5, -4),
        )

        model = normalize_shape(shape)
        self.assertIsInstance(model.root, HoleIR)
        self.assertEqual(model.root.placement.mode, "anchored")
        self.assertEqual(model.root.placement.parent_anchor, "bottom")
        self.assertEqual(model.root.placement.child_anchor, "bottom")

        commands = compile_solidcraft_ir(
            model,
            "BottomHole",
        )["commands"]
        circle = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.circle.center"
        )
        self.assertEqual(circle["center"], [5.0, -4.0])
        cut = commands[-1]["params"]
        self.assertEqual(cut["distance"], 3)
        self.assertEqual(cut["direction"], "positive")
        self.assertEqual(cut["name"], "Hole")

    def test_backend_unsupported_anchored_holes_remain_typed(self):
        plate = Box(40, 30, 10, anchor=Anchor.BOTTOM)
        cases = (
            (
                plate + Hole(d=4).on(
                    plate,
                    face=Faces.LEFT,
                ),
                "TOP or BOTTOM",
            ),
            (
                plate + CounterboreHole(
                    d=4,
                    counterbore_d=8,
                    counterbore_depth=2,
                ).attach(
                    plate,
                    parent=Anchor.TOP,
                    child=Anchor.BOTTOM,
                ),
                "simple",
            ),
        )
        for index, (shape, error) in enumerate(cases):
            with self.subTest(index=index):
                model = normalize_shape(shape)
                self.assertIsInstance(model.root, HoleIR)
                self.assertIsInstance(
                    model.root.placement,
                    FeaturePlacementIR,
                )
                with self.assertRaisesRegex(ModelError, error):
                    compile_solidcraft_ir(
                        model,
                        f"UnsupportedAnchoredHole{index}",
                    )
                with self.assertRaisesRegex(ModelError, "HoleIR"):
                    compile_mitcad_ir(
                        model,
                        f"UnsupportedAnchoredHole{index}",
                    )

    def test_countersink_angle_parameter_has_semantic_angle_role(self):
        sink_angle = Parameter("sink_angle", 90)
        plate = Box(40, 30, 10, anchor=Anchor.BOTTOM)
        shape = plate + CountersinkHole(
            d=5,
            countersink_d=10,
            countersink_angle=sink_angle,
            direction=(0, 0, -1),
        ).at(0, 0, 10)

        model = self.assert_solidcraft_compatibility(
            shape,
            "ParameterizedCountersink",
        )
        self.assertIsInstance(model.root, HoleIR)
        self.assertIs(model.root.countersink_angle, sink_angle)
        self.assertEqual(
            model.parameters,
            (
                ParameterIR(
                    "sink_angle",
                    90,
                    roles=("angle",),
                ),
            ),
        )

        commands = compile_solidcraft_ir(
            model,
            "ParameterizedCountersink",
        )["commands"]
        parameter = next(
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        )
        self.assertEqual(parameter["name"], "sink_angle")
        self.assertEqual(parameter["unit"], "deg")
        hole = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.hole"
        )
        self.assertEqual(hole["cs_angle"], "sink_angle")

    def test_circular_hole_pattern_is_semantic_feature_history(self):
        bolts = Parameter("bolts", 6)
        pcd = Parameter("pcd", 60)
        plate = Box(100, 100, 6, anchor=Anchor.BOTTOM)
        source = Hole(
            d=8,
            direction=(0, 0, -1),
        ).at(pcd / 2, 0, 6)
        plate = plate + source
        shape = plate.circular_pattern(
            source,
            count=bolts,
            axis=Axis.Z,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "CircularHolePattern",
        )
        self.assertIsInstance(model.root, CircularPatternIR)
        self.assertIsInstance(model.root.base, HoleIR)
        self.assertEqual(
            model.root.sources,
            (FeatureRefIR(("root",)),),
        )
        self.assertIs(
            resolve_feature_ref(
                model.root.base,
                model.root.sources[0],
            ),
            model.root.base,
        )
        self.assertEqual(model.root.axis, AxisLineIR("Z"))
        self.assertIs(model.root.count, bolts)
        self.assertEqual(
            model.parameters,
            (
                ParameterIR("pcd", 60, roles=("length",)),
                ParameterIR("bolts", 6, roles=("count",)),
            ),
        )

        pattern = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "CircularHolePattern",
            )["commands"]
            if row["command"] == "solid.pattern.circular"
        )
        self.assertEqual(
            pattern,
            {
                "features": ["Hole1"],
                "axis": "Z",
                "count": "bolts",
                "alignment": "right",
                "reversed": False,
            },
        )
        with self.assertRaisesRegex(ModelError, "CircularPatternIR"):
            compile_mitcad_ir(model, "CircularHolePattern")

    def test_rectangular_hole_pattern_keeps_two_direction_semantics(self):
        columns = Parameter("columns", 3)
        pitch = Parameter("pitch", 20)
        plate = Box(100, 80, 6, anchor=Anchor.BOTTOM)
        source = Hole(
            d=6,
            direction=(0, 0, -1),
        ).at(-20, -14, 6)
        plate = plate + source
        shape = plate.rectangular_pattern(
            source,
            count=columns,
            spacing=pitch,
            direction=Axis.X,
            count2=2,
            spacing2=28,
            direction2=Axis.Y,
            alignment="center",
            alignment2="left",
            reversed=True,
            reversed2=True,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "RectangularHolePattern",
        )
        self.assertIsInstance(model.root, RectangularPatternIR)
        self.assertEqual(model.root.direction1, (1.0, 0.0, 0.0))
        self.assertEqual(model.root.direction2, (0.0, 1.0, 0.0))
        self.assertEqual(model.root.alignment1, "center")
        self.assertEqual(model.root.alignment2, "left")
        self.assertTrue(model.root.reversed1)
        self.assertTrue(model.root.reversed2)
        self.assertEqual(
            model.parameters,
            (
                ParameterIR("columns", 3, roles=("count",)),
                ParameterIR("pitch", 20, roles=("length",)),
            ),
        )

        pattern = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "RectangularHolePattern",
            )["commands"]
            if row["command"] == "solid.pattern.rectangular"
        )
        self.assertEqual(pattern["features"], ["Hole1"])
        self.assertEqual(pattern["count1"], "columns")
        self.assertEqual(pattern["spacing1"], "pitch")
        self.assertEqual(pattern["alignment"], "center")
        self.assertTrue(pattern["reversed"])
        self.assertEqual(pattern["count2"], 2)
        self.assertEqual(pattern["spacing2"], 28)
        self.assertEqual(pattern["alignment2"], "left")
        self.assertTrue(pattern["reversed2"])

    def test_circular_pattern_preserves_shifted_custom_axis_and_angle(self):
        sweep = Parameter("pattern_sweep", 180)
        plate = Box(80, 80, 6, anchor=Anchor.BOTTOM)
        source = Hole(
            d=5,
            direction=(0, 0, -1),
        ).at(15, 0, 6)
        plate = plate + source
        shape = plate.circular_pattern(
            source,
            count=4,
            axis=AxisLine((0, 1, 1), origin=(5, 0, 0)),
            angle=sweep,
            alignment="left",
            reversed=True,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "CustomAxisPattern",
        )
        self.assertIsInstance(model.root, CircularPatternIR)
        self.assertEqual(model.root.axis.direction, (0.0, 1.0, 1.0))
        self.assertEqual(model.root.axis.origin, (5, 0, 0))
        self.assertEqual(
            model.parameters,
            (ParameterIR("pattern_sweep", 180, roles=("angle",)),),
        )
        pattern = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "CustomAxisPattern",
            )["commands"]
            if row["command"] == "solid.pattern.circular"
        )
        self.assertEqual(
            pattern["axis"],
            {"origin": [5, 0, 0], "dir": [0.0, 1.0, 1.0]},
        )
        self.assertEqual(pattern["angle"], "pattern_sweep")
        self.assertEqual(pattern["alignment"], "left")
        self.assertTrue(pattern["reversed"])

    def test_circular_pattern_axisline_keeps_symbolic_origin_and_fixed_vector(self):
        axis_x = Parameter("pattern_axis_x", 5)
        axis_z = Parameter("pattern_axis_z", 7)
        plate = Box(80, 80, 6, anchor=Anchor.BOTTOM)
        source = Hole(
            d=5,
            direction=(0, 0, -1),
        ).at(15, 0, 6)
        plate = plate + source
        shape = plate.circular_pattern(
            source,
            count=4,
            axis=AxisLine(
                (0, 1, 1),
                origin=(axis_x, 0, axis_z),
            ),
            angle=180,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "SymbolicAxisPattern",
        )

        self.assertIsInstance(model.root, CircularPatternIR)
        self.assertEqual(model.root.axis.direction, (0.0, 1.0, 1.0))
        self.assertIs(model.root.axis.origin[0], axis_x)
        self.assertIs(model.root.axis.origin[2], axis_z)
        self.assertEqual(
            [
                (parameter.name, parameter.roles)
                for parameter in model.parameters
            ],
            [
                ("pattern_axis_x", ("length",)),
                ("pattern_axis_z", ("length",)),
            ],
        )
        pattern = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "SymbolicAxisPattern",
            )["commands"]
            if row["command"] == "solid.pattern.circular"
        )
        self.assertEqual(
            pattern["axis"],
            {
                "origin": ["pattern_axis_x", 0, "pattern_axis_z"],
                "dir": [0.0, 1.0, 1.0],
            },
        )

    def test_pattern_with_text_extrude_source_is_typed_history(self):
        from scpf.core import Text2D

        with Sketch(name="TypedText", plane="XY") as sketch:
            Text2D("A", height=8)
        source = sketch.extrude(5)
        body = source.rectangular_pattern(
            source,
            count=2,
            spacing=30,
            direction=Axis.X,
        )
        model = normalize_shape(body)
        self.assertIsInstance(model.root, RectangularPatternIR)
        self.assertIsInstance(model.root.base, ExtrudeIR)
        self.assertIsInstance(
            model.root.base.sketch.graph.entities[0],
            TextEntityIR,
        )
        pattern = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "TypedTextPattern",
            )["commands"]
            if row["command"] == "solid.pattern.rectangular"
        )
        self.assertEqual(pattern["features"], ["Extrude1"])
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "TypedTextPattern")

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

    def test_shell_and_hole_compose_over_generic_body_ir(self):
        chamfered = Box(
            80,
            50,
            20,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            1,
            edges=Edges.from_faces(Faces.TOP),
        )
        shelled = chamfered.shell(
            2,
            open=Faces.FRONT,
        )
        shell_model = self.assert_solidcraft_compatibility(
            shelled,
            "ChamferShell",
        )
        self.assertIsInstance(shell_model.root, ShellIR)
        self.assertIsInstance(shell_model.root.base, ChamferIR)

        shell_commands = compile_solidcraft_ir(
            shell_model,
            "ChamferShell",
        )["commands"]
        face_bind_names = [
            next(iter(row.get("bind", {})))
            for row in shell_commands
            if row["command"] == "model.faces"
        ]
        self.assertEqual(
            face_bind_names,
            ["$topology_face_1", "$topology_face_name_2"],
        )

        drilled = (
            chamfered
            + Hole(
                d=5,
                direction=(0, 0, -1),
            ).at(0, 0, 20)
        )
        hole_model = self.assert_solidcraft_compatibility(
            drilled,
            "ChamferHole",
        )
        self.assertIsInstance(hole_model.root, HoleIR)
        self.assertIsInstance(hole_model.root.target, BodyIR)
        self.assertIsInstance(hole_model.root.target, ChamferIR)

        with self.assertRaisesRegex(ModelError, "HoleIR"):
            compile_mitcad_ir(hole_model, "ChamferHole")

    def test_explicit_hole_family_is_semantic_hole_history(self):
        hole_d = Parameter("hole_d", 6)
        hole_depth = Parameter("hole_depth", 8)
        cb_d = Parameter("cb_d", 12)
        cb_depth = Parameter("cb_depth", 4)
        cs_d = Parameter("cs_d", 12)
        thread_depth = Parameter("thread_depth", 10)

        body = Box(120, 40, 12, anchor=Anchor.BOTTOM)
        features = (
            Hole(
                d=hole_d,
                depth=hole_depth,
                direction=(0, 0, -1),
            ).at(-45, 0, 12),
            CounterboreHole(
                d=6,
                counterbore_d=cb_d,
                counterbore_depth=cb_depth,
                direction=(0, 0, -1),
            ).at(-15, 0, 12),
            CountersinkHole(
                d=6,
                countersink_d=cs_d,
                countersink_angle=90,
                direction=(0, 0, -1),
            ).at(15, 0, 12),
            ThreadedHole(
                thread="M6",
                d=5,
                direction=(0, 0, -1),
                thread_depth=thread_depth,
                modeled=True,
                ease_out="short",
            ).at(45, 0, 12),
        )
        for feature in features:
            body = body + feature

        model = self.assert_solidcraft_compatibility(
            body,
            "TypedHoleFamily",
        )
        self.assertIsInstance(model.root, HoleIR)

        holes = []
        current = model.root
        while isinstance(current, HoleIR):
            holes.append(current)
            current = current.target
        holes.reverse()

        self.assertEqual(len(holes), 4)
        self.assertIsInstance(current, PlacementIR)
        self.assertIsInstance(current.primitive, BoxIR)
        self.assertEqual(
            [hole.hole_type for hole in holes],
            ["simple", "counterbore", "countersink", "threaded"],
        )

        simple, counterbore, countersink, threaded = holes
        self.assertIs(simple.diameter, hole_d)
        self.assertEqual(simple.depth_mode, "distance")
        self.assertIs(simple.depth, hole_depth)
        self.assertEqual(simple.direction, (0.0, 0.0, -1.0))
        self.assertIs(counterbore.counterbore_diameter, cb_d)
        self.assertIs(counterbore.counterbore_depth, cb_depth)
        self.assertIs(countersink.countersink_diameter, cs_d)
        self.assertEqual(countersink.countersink_angle, 90.0)
        self.assertEqual(threaded.thread, "M6")
        self.assertIs(threaded.thread_depth, thread_depth)
        self.assertTrue(threaded.modeled)
        self.assertEqual(threaded.ease_out, "short")

        self.assertEqual(
            model.parameters,
            (
                ParameterIR("hole_d", 6, roles=("length",)),
                ParameterIR("hole_depth", 8, roles=("length",)),
                ParameterIR("cb_d", 12, roles=("length",)),
                ParameterIR("cb_depth", 4, roles=("length",)),
                ParameterIR("cs_d", 12, roles=("length",)),
                ParameterIR("thread_depth", 10, roles=("length",)),
            ),
        )

        solidcraft = compile_solidcraft_ir(model, "TypedHoleFamily")
        hole_commands = [
            row["params"]
            for row in solidcraft["commands"]
            if row["command"] == "solid.hole"
        ]
        self.assertEqual(len(hole_commands), 4)
        self.assertEqual(hole_commands[0]["depth"], "hole_depth")
        self.assertEqual(hole_commands[1]["cb_diameter"], "cb_d")
        self.assertEqual(hole_commands[2]["cs_diameter"], "cs_d")
        self.assertEqual(hole_commands[3]["thread_depth"], "thread_depth")

        with self.assertRaisesRegex(ModelError, "HoleIR"):
            compile_mitcad_ir(model, "TypedHoleFamily")

    def test_explicit_hole_without_direction_preserves_auto_inward_intent(self):
        body = (
            Box(40, 30, 10, anchor=Anchor.BOTTOM)
            + Hole(d=5).at(0, 0, 10)
        )
        model = self.assert_solidcraft_compatibility(
            body,
            "AutoInwardHole",
        )
        self.assertIsInstance(model.root, HoleIR)
        self.assertIsNone(model.root.direction)
        self.assertEqual(model.root.depth_mode, "through_all")
        self.assertIsNone(model.root.depth)

        hole = next(
            row["params"]
            for row in compile_solidcraft_ir(
                model,
                "AutoInwardHole",
            )["commands"]
            if row["command"] == "solid.hole"
        )
        self.assertNotIn("direction", hole)
        self.assertNotIn("depth", hole)

    def test_hole_ir_accepts_generic_typed_body_target(self):
        shape = (
            Cylinder(d=30, h=12, anchor=Anchor.BOTTOM)
            + Hole(d=5, direction=(0, 0, -1)).at(0, 0, 12)
        )
        model = self.assert_solidcraft_compatibility(
            shape,
            "CylinderHole",
        )
        self.assertIsInstance(model.root, HoleIR)
        self.assertIsInstance(model.root.target, BodyIR)
        self.assertIsInstance(model.root.target, PlacementIR)
        self.assertIsInstance(model.root.target.primitive, CylinderIR)
        with self.assertRaisesRegex(ModelError, "HoleIR"):
            compile_mitcad_ir(model, "CylinderHole")

    def test_parameter_driven_hole_direction_stays_fail_closed(self):
        direction_parameter = Parameter("drill_direction", -1)
        shape = (
            Box(30, 30, 12, anchor=Anchor.BOTTOM)
            + Hole(
                d=5,
                direction=(0, 0, direction_parameter),
            ).at(0, 0, 12)
        )
        model = normalize_shape(shape)
        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "ParameterizedHoleDirection")

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

    def test_shared_modify_selectors_are_semantic_and_solidcraft_compatible(self):
        direction_shape = Box(
            80,
            50,
            8,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            2,
            edges=FRONT + LEFT,
        )
        direction_model = self.assert_solidcraft_compatibility(
            direction_shape,
            "DirectionChamfer",
        )
        self.assertIsInstance(direction_model.root, ChamferIR)
        self.assertEqual(
            direction_model.root.edges,
            DirectionPairEdgeSetIR(((-1, -1, 0),)),
        )

        explicit_shape = Box(
            80,
            50,
            8,
            anchor=Anchor.BOTTOM,
        ).fillet(
            2,
            edges=[(-40, -25, 0)],
        )
        explicit_model = self.assert_solidcraft_compatibility(
            explicit_shape,
            "ExplicitFillet",
        )
        self.assertIsInstance(explicit_model.root, FilletIR)
        self.assertEqual(
            explicit_model.root.edges,
            ExplicitEdgePicksIR(((-40, -25, 0),)),
        )

        face_shape = Box(
            80,
            50,
            8,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            1,
            edges=Edges.from_faces(Faces.TOP, Faces.FRONT),
        )
        face_model = self.assert_solidcraft_compatibility(
            face_shape,
            "MultiFaceChamfer",
        )
        self.assertEqual(
            face_model.root.edges,
            FaceBoundaryIR(("top", "front")),
        )

        for model, name in (
            (direction_model, "DirectionChamfer"),
            (explicit_model, "ExplicitFillet"),
        ):
            with self.subTest(name=name):
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(model, name)

        mitcad_face = compile_mitcad_ir(
            face_model,
            "MultiFaceChamfer",
        )
        self.assertEqual(
            len(
                mitcad_face["replay"][0][
                    "bind_face_boundary_edges"
                ]["faces"]
            ),
            2,
        )

    def test_named_polygon_modify_selectors_are_semantic_and_compatible(self):
        with Sketch(name="ProfileEdges", plane="XZ") as sketch:
            Polygon2D(
                [
                    ("start", (0, 0)),
                    ("tip", (10, 0)),
                    ("far", (10, 8)),
                    ("end", (0, 8)),
                ],
                plane="XZ",
                world=True,
            )
        body = sketch.extrude(8, sym=True)

        segment_model = self.assert_solidcraft_compatibility(
            body.chamfer(
                0.5,
                edges=Edges.from_profile("start"),
            ),
            "ProfileSegmentChamfer",
        )
        self.assertIsInstance(segment_model.root, ChamferIR)
        self.assertEqual(
            segment_model.root.edges,
            ProfileEdgeSetIR(
                patterns=("start",),
                kind="segments",
                sides="both",
            ),
        )

        vertex_model = self.assert_solidcraft_compatibility(
            body.fillet(
                0.5,
                edges=Edges.from_vertices("tip", "end"),
            ),
            "ProfileVertexFillet",
        )
        self.assertIsInstance(vertex_model.root, FilletIR)
        self.assertEqual(
            vertex_model.root.edges,
            ProfileEdgeSetIR(
                patterns=("tip", "end"),
                kind="vertices",
                sides="axis",
            ),
        )

        for model, name in (
            (segment_model, "ProfileSegmentChamfer"),
            (vertex_model, "ProfileVertexFillet"),
        ):
            with self.subTest(name=name):
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(model, name)

    def test_vertical_box_fillet_is_semantic_parallel_edge_ir(self):
        radius = Parameter("fillet_radius", 2)
        shape = Box(
            50,
            40,
            20,
            anchor=Anchor.BOTTOM,
        ).fillet(
            radius,
            edges=Edges.VERTICAL,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "VerticalBoxFillet",
        )
        self.assertIsInstance(model.root, FilletIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertIsInstance(model.root.base.primitive, BoxIR)
        self.assertIs(model.root.radius, radius)
        self.assertEqual(model.root.edges, ParallelEdgeSetIR("Z"))
        self.assertEqual(
            model.parameters,
            (
                ParameterIR(
                    "fillet_radius",
                    2,
                    roles=("length",),
                ),
            ),
        )

        solidcraft = compile_solidcraft_ir(model, "VerticalBoxFillet")
        fillet = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.fillet"
        )
        self.assertEqual(
            fillet["params"]["edges"],
            [
                [-25.0, -20.0, 10.0],
                [25.0, -20.0, 10.0],
                [25.0, 20.0, 10.0],
                [-25.0, 20.0, 10.0],
            ],
        )
        self.assertEqual(fillet["params"]["radius"], "fillet_radius")
        self.assertEqual(fillet["params"]["body"], "VerticalBoxFillet")

        mitcad = compile_mitcad_ir(model, "VerticalBoxFillet")
        self.assertEqual(
            [
                row["def"]["type"]
                for row in mitcad["commands"]
                if row["cmd"] == "add_feature"
            ],
            ["box"],
        )
        self.assertEqual(len(mitcad["replay"]), 1)
        stage = mitcad["replay"][0]
        self.assertEqual(
            stage["bind_parallel_edges"],
            {
                "name": "parallel_edges",
                "body": "body",
                "axis": "Z",
                "expected": 4,
            },
        )
        fillet_def = stage["commands"][0]["def"]
        self.assertEqual(fillet_def["type"], "fillet")
        self.assertEqual(
            fillet_def["edges"],
            {"$mitcad_bind": "parallel_edges"},
        )
        self.assertEqual(fillet_def["radius"], "fillet_radius")

    def test_fillet_cone_join_preserves_semantic_feature_order(self):
        filleted = Box(
            50,
            40,
            20,
            anchor=Anchor.BOTTOM,
        ).fillet(
            2,
            edges=Edges.VERTICAL,
        )
        cone = Cone(
            d=18,
            top_d=10,
            h=8,
            anchor=Anchor.BOTTOM,
        ).at(
            0,
            0,
            18,
            anchor=Anchor.BOTTOM,
        )
        shape = filleted + cone

        model = self.assert_solidcraft_compatibility(
            shape,
            "FilletConeJoin",
        )
        self.assertIsInstance(model.root, BooleanIR)
        self.assertEqual(model.root.operation, "join")
        self.assertIsInstance(model.root.target, FilletIR)
        self.assertEqual(
            model.root.target.edges,
            ParallelEdgeSetIR("Z"),
        )
        self.assertIsInstance(model.root.tool, PlacementIR)
        self.assertIsInstance(model.root.tool.primitive, ConeIR)

        solidcraft = compile_solidcraft_ir(model, "FilletConeJoin")
        geometry = [
            row
            for row in solidcraft["commands"]
            if row["command"].startswith("solid.")
        ]
        self.assertEqual(
            [row["command"] for row in geometry],
            ["solid.box", "solid.fillet", "solid.cone"],
        )
        self.assertEqual(geometry[-1]["params"]["operation"], "join")
        self.assertEqual(
            geometry[-1]["params"]["targets"],
            ["FilletConeJoin"],
        )

        mitcad = compile_mitcad_ir(model, "FilletConeJoin")
        self.assertEqual(
            [
                row["def"]["type"]
                for row in mitcad["commands"]
                if row["cmd"] == "add_feature"
            ],
            ["box"],
        )
        stage = mitcad["replay"][0]
        self.assertEqual(stage["bind_parallel_edges"]["axis"], "Z")
        self.assertEqual(stage["bind_parallel_edges"]["expected"], 4)
        self.assertEqual(
            [
                row["def"]["type"]
                for row in stage["commands"]
                if row["cmd"] == "add_feature"
            ],
            ["fillet", "construction_plane", "cone"],
        )
        cone_def = stage["commands"][-1]["def"]
        self.assertEqual(cone_def["operation"], "join")
        self.assertEqual(cone_def["participants"], [])

    def test_top_face_boundary_fillet_reuses_semantic_face_selector(self):
        radius = Parameter("top_fillet_radius", 2)
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).fillet(
            radius,
            edges=Edges.from_faces(Faces.TOP),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "TopFaceBoundaryFillet",
        )
        self.assertIsInstance(model.root, FilletIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertIsInstance(model.root.base.primitive, BoxIR)
        self.assertIs(model.root.radius, radius)
        self.assertEqual(
            model.root.edges,
            FaceBoundaryIR(("top",)),
        )
        self.assertEqual(
            model.parameters,
            (
                ParameterIR(
                    "top_fillet_radius",
                    2,
                    roles=("length",),
                ),
            ),
        )

        solidcraft = compile_solidcraft_ir(
            model,
            "TopFaceBoundaryFillet",
        )
        self.assertEqual(
            [
                row["command"]
                for row in solidcraft["commands"]
                if row["command"].startswith(("solid.", "model."))
            ],
            ["solid.box", "model.faces", "model.edges", "solid.fillet"],
        )
        fillet = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.fillet"
        )
        self.assertEqual(fillet["params"]["edges"], "$topology_edges_1")
        self.assertEqual(
            fillet["params"]["radius"],
            "top_fillet_radius",
        )

        mitcad = compile_mitcad_ir(model, "TopFaceBoundaryFillet")
        stage = mitcad["replay"][0]
        self.assertNotIn("bind_parallel_edges", stage)
        self.assertEqual(
            stage["bind_face_boundary_edges"],
            {
                "name": "edges",
                "body": "body",
                "face": {
                    "surface": "plane",
                    "normal": [0, 0, 1],
                    "normal_tolerance": 1e-6,
                },
            },
        )
        fillet_def = stage["commands"][0]["def"]
        self.assertEqual(fillet_def["type"], "fillet")
        self.assertEqual(
            fillet_def["edges"],
            {"$mitcad_bind": "edges"},
        )
        self.assertEqual(
            fillet_def["radius"],
            "top_fillet_radius",
        )

    def test_other_face_boundary_fillet_selectors_are_typed(self):
        for index, faces in enumerate(
            (
                (Faces.FRONT,),
                (Faces.TOP, Faces.FRONT),
            ),
            start=1,
        ):
            with self.subTest(faces=faces):
                shape = Box(
                    60,
                    40,
                    12,
                    anchor=Anchor.BOTTOM,
                ).fillet(
                    2,
                    edges=Edges.from_faces(*faces),
                )
                model = self.assert_solidcraft_compatibility(
                    shape,
                    f"TypedFaceBoundaryFillet{index}",
                )
                self.assertIsInstance(model.root, FilletIR)
                self.assertEqual(
                    model.root.edges,
                    FaceBoundaryIR(
                        tuple(face.value for face in faces)
                    ),
                )
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(
                        model,
                        f"TypedFaceBoundaryFillet{index}",
                    )

    def test_face_boundary_fillet_over_non_box_is_typed(self):
        shape = Cylinder(
            d=30,
            h=12,
            anchor=Anchor.BOTTOM,
        ).fillet(
            2,
            edges=Edges.from_faces(Faces.TOP),
        )
        model = self.assert_solidcraft_compatibility(
            shape,
            "CylinderFaceBoundaryFillet",
        )
        self.assertIsInstance(model.root, FilletIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertIsInstance(model.root.base.primitive, CylinderIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "CylinderFaceBoundaryFillet")

    def test_top_face_boundary_fillet_cone_join_is_typed_boolean(self):
        filleted = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).fillet(
            2,
            edges=Edges.from_faces(Faces.TOP),
        )
        cone = Cone(
            d=12,
            top_d=6,
            h=6,
            anchor=Anchor.BOTTOM,
        ).at(
            0,
            0,
            12,
            anchor=Anchor.BOTTOM,
        )
        shape = filleted + cone
        model = self.assert_solidcraft_compatibility(
            shape,
            "FaceBoundaryFilletCone",
        )
        self.assertIsInstance(model.root, BooleanIR)
        self.assertIsInstance(model.root.target, FilletIR)
        self.assertIsInstance(model.root.tool, PlacementIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "UnsupportedFaceBoundaryFilletCone")

    def test_circle_extrude_is_separate_sketch_region_and_extrude_ir(self):
        diameter = Parameter("diameter", 20)
        height = Parameter("height", 30)
        with Sketch(name="Profile", plane="XY") as sketch:
            Circle2D(d=diameter)
        shape = sketch.extrude(-height)

        model = self.assert_solidcraft_compatibility(
            shape,
            "NegativeCircleExtrude",
        )
        self.assertIsInstance(model.root, ExtrudeIR)
        self.assertIsInstance(model.root.sketch, SketchIR)
        self.assertEqual(model.root.sketch.name, "Profile")
        self.assertEqual(
            model.root.sketch.plane,
            PlaneIR(orientation="XY", origin=(0, 0, 0)),
        )
        self.assertEqual(len(model.root.sketch.profiles), 1)
        profile = model.root.sketch.profiles[0]
        self.assertIsInstance(profile, CircleProfileIR)
        self.assertEqual(profile.diameter, diameter)
        self.assertEqual(profile.center, (0, 0))
        self.assertEqual(model.root.regions, (RegionIR(outer=0),))
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

    def test_annular_profile_extrude_is_two_profiles_one_semantic_region(self):
        outer = Parameter("outer_diameter", 10)
        inner = Parameter("inner_diameter", 8)
        length = Parameter("length", 30)
        with Sketch(name="Tube profile", plane="XY") as sketch:
            Circle2D(d=outer)
            Circle2D(d=inner)

        shape = sketch.extrude(
            length,
            profiles=[(4.5, 0)],
            exact_regions=True,
        )
        model = self.assert_solidcraft_compatibility(shape, "Tube")

        self.assertIsInstance(model.root, ExtrudeIR)
        self.assertEqual(len(model.root.sketch.profiles), 2)
        self.assertEqual(
            [profile.diameter for profile in model.root.sketch.profiles],
            [outer, inner],
        )
        self.assertEqual(
            model.root.regions,
            (RegionIR(outer=0, holes=(1,)),),
        )
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["outer_diameter", "inner_diameter", "length"],
        )

        mitcad = compile_mitcad_ir(model, "Tube")
        sketch_def = mitcad["commands"][-2]["def"]
        extrude_def = mitcad["commands"][-1]["def"]
        self.assertEqual(sketch_def["type"], "sketch")
        self.assertEqual(
            [entity["type"] for entity in sketch_def["entities"]],
            ["point", "circle", "circle"],
        )
        self.assertEqual(
            [dimension["value"] for dimension in sketch_def["dimensions"]],
            ["outer_diameter", "inner_diameter"],
        )
        self.assertEqual(extrude_def["type"], "extrude")
        self.assertEqual(
            extrude_def["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [4.5, 0.0]}],
        )
        self.assertEqual(
            extrude_def["extent"]["distance"],
            "length",
        )

    def test_annular_region_invalid_membership_fails_before_native_execution(self):
        cases = (
            ModelIR(
                root=ExtrudeIR(
                    sketch=SketchIR(
                        name="MissingHole",
                        plane=PlaneIR(orientation="XY"),
                        profiles=(
                            CircleProfileIR(diameter=10),
                            CircleProfileIR(diameter=8),
                        ),
                    ),
                    regions=(RegionIR(outer=0, holes=(2,)),),
                    distance=20,
                    direction="positive",
                ),
                parameters=(),
            ),
            ModelIR(
                root=ExtrudeIR(
                    sketch=SketchIR(
                        name="InsideOut",
                        plane=PlaneIR(orientation="XY"),
                        profiles=(
                            CircleProfileIR(diameter=8),
                            CircleProfileIR(diameter=10),
                        ),
                    ),
                    regions=(RegionIR(outer=0, holes=(1,)),),
                    distance=20,
                    direction="positive",
                ),
                parameters=(),
            ),
            ModelIR(
                root=ExtrudeIR(
                    sketch=SketchIR(
                        name="SkippedBoundary",
                        plane=PlaneIR(orientation="XY"),
                        profiles=(
                            CircleProfileIR(diameter=10),
                            CircleProfileIR(diameter=8),
                            CircleProfileIR(diameter=6),
                        ),
                    ),
                    regions=(RegionIR(outer=0, holes=(2,)),),
                    distance=20,
                    direction="positive",
                ),
                parameters=(),
            ),
        )

        for model in cases:
            for compiler in (compile_solidcraft_ir, compile_mitcad_ir):
                with self.subTest(model=model.root.sketch.name, compiler=compiler):
                    with self.assertRaises(ModelError):
                        compiler(model, model.root.sketch.name)

    def test_three_profile_exact_region_is_typed_boundary_membership(self):
        with Sketch(name="Three circles", plane="XY") as sketch:
            Circle2D(d=10)
            Circle2D(d=8)
            Circle2D(d=6)
        shape = sketch.extrude(
            20,
            profiles=[(4.5, 0)],
            exact_regions=True,
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "ThreeCircles",
        )
        self.assertIsInstance(model.root, ExtrudeIR)
        self.assertEqual(len(model.root.sketch.profiles), 3)
        self.assertTrue(
            all(
                isinstance(profile, CircleProfileIR)
                for profile in model.root.sketch.profiles
            )
        )
        self.assertEqual(
            model.root.regions,
            (RegionIR(outer=0, holes=(1,)),),
        )
        self.assertNotIn(2, model.root.regions[0].holes)

        mitcad = compile_mitcad_ir(model, "ThreeCircles")
        sketch_def = mitcad["commands"][-2]["def"]
        extrude_def = mitcad["commands"][-1]["def"]
        self.assertEqual(
            [entity["type"] for entity in sketch_def["entities"]],
            ["point", "circle", "circle", "circle"],
        )
        self.assertEqual(
            [dimension["value"] for dimension in sketch_def["dimensions"]],
            [10, 8, 6],
        )
        self.assertEqual(
            extrude_def["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [4.5, 0.0]}],
        )

    def test_three_profile_exact_region_can_select_innermost_disk(self):
        with Sketch(name="Three circles inner", plane="XY") as sketch:
            Circle2D(d=10)
            Circle2D(d=8)
            Circle2D(d=6)
        shape = sketch.extrude(
            20,
            profiles=[(2, 0)],
            exact_regions=True,
        )

        model = normalize_shape(shape)
        self.assertIsInstance(model.root, ExtrudeIR)
        self.assertEqual(
            model.root.regions,
            (RegionIR(outer=2),),
        )

        solidcraft = compile_solidcraft_ir(model, "InnerDisk")
        self.assertEqual(
            solidcraft["commands"][-1]["params"]["profiles"],
            [{"point": [0.0, 0.0]}],
        )
        self.assertTrue(solidcraft["commands"][-1]["params"]["exact_regions"])

        mitcad = compile_mitcad_ir(model, "InnerDisk")
        self.assertEqual(
            mitcad["commands"][-1]["def"]["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [0.0, 0.0]}],
        )

    def test_multi_circle_exact_region_rejects_boundary_or_outside_pick(self):
        for pick in ((5, 0), (6, 0)):
            with self.subTest(pick=pick):
                with Sketch(name="Invalid circle pick", plane="XY") as sketch:
                    Circle2D(d=10)
                    Circle2D(d=8)
                    Circle2D(d=6)
                model = normalize_shape(
                    sketch.extrude(
                        20,
                        profiles=[pick],
                        exact_regions=True,
                    )
                )
                self.assertIsInstance(model.root, LegacyShapeIR)
                with self.assertRaises(ModelError):
                    compile_mitcad_ir(model, "InvalidCirclePick")

    def test_region_ir_rejects_invalid_profile_membership(self):
        for kwargs in (
            {"outer": -1},
            {"outer": True},
            {"outer": 0, "holes": [1]},
            {"outer": 0, "holes": (-1,)},
            {"outer": 0, "holes": (0,)},
            {"outer": 0, "holes": (1, 1)},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RegionIR(**kwargs)

    def test_polygon_symmetric_extrude_chamfer_composes_typed_ir(self):
        with Sketch(name="Hook profile", plane="XZ") as sketch:
            Polygon2D(
                [(-20, 0), (20, 0), (20, 30), (-20, 30)],
                plane="XZ",
                world=True,
            )
        shape = sketch.extrude(15, sym=True).chamfer(
            1.5,
            edges=Edges.from_faces(Faces.FRONT, Faces.BACK),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "TopologyFaceBoundaryXz",
        )
        self.assertIsInstance(model.root, ChamferIR)
        self.assertIsInstance(model.root.base, ExtrudeIR)
        extrusion = model.root.base
        self.assertEqual(extrusion.direction, "symmetric")
        self.assertEqual(extrusion.distance, 15)
        self.assertEqual(
            extrusion.sketch.plane,
            PlaneIR(orientation="XZ", origin=(0, 0, 0)),
        )
        self.assertEqual(len(extrusion.sketch.profiles), 1)
        profile = extrusion.sketch.profiles[0]
        self.assertIsInstance(profile, PolygonProfileIR)
        self.assertEqual(
            profile.points,
            ((-20, 0), (20, 0), (20, -30), (-20, -30)),
        )
        self.assertEqual(extrusion.regions, (RegionIR(outer=0),))
        self.assertEqual(model.root.edges.faces, ("front", "back"))

        mitcad = compile_mitcad_ir(model, "TopologyFaceBoundaryXz")
        sketch_def = mitcad["commands"][-2]["def"]
        extrude_def = mitcad["commands"][-1]["def"]
        self.assertEqual(sketch_def["type"], "sketch")
        self.assertEqual(
            [entity["type"] for entity in sketch_def["entities"]],
            ["point", "point", "point", "point",
             "line", "line", "line", "line"],
        )
        self.assertEqual(
            [
                (entity["start"], entity["end"])
                for entity in sketch_def["entities"][4:]
            ],
            [
                ("p1", "p2"),
                ("p2", "p3"),
                ("p3", "p4"),
                ("p4", "p1"),
            ],
        )
        self.assertEqual(
            extrude_def["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [0.0, -15.0]}],
        )
        self.assertEqual(
            extrude_def["extent"],
            {"type": "symmetric", "distance": 15, "full_length": True},
        )
        stage = mitcad["replay"][0]
        self.assertEqual(
            [
                face["normal"]
                for face in stage["bind_face_boundary_edges"]["faces"]
            ],
            [[0, -1, 0], [0, 1, 0]],
        )
        self.assertEqual(len(stage["commands"]), 1)
        self.assertEqual(stage["commands"][0]["def"]["type"], "chamfer")
        self.assertEqual(
            stage["commands"][0]["def"]["size"],
            {"type": "equal_distance", "distance": 1.5},
        )

    def test_simple_concave_polygon_region_is_typed_for_extrude(self):
        with Sketch(name="Concave", plane="XY") as sketch:
            Polygon2D(
                [(0, 0), (20, 0), (5, 10), (20, 30), (0, 30)],
                plane="XY",
            )
        shape = sketch.extrude(10, sym=True)
        model = normalize_shape(shape)
        self.assertIsInstance(model.root, ExtrudeIR)
        self.assertEqual(
            compile_solidcraft_ir(model, "ConcavePolygon"),
            _compile_shape_legacy_with_dependencies(
                shape,
                "ConcavePolygon",
            )[0],
        )
        mitcad = compile_mitcad_ir(model, "ConcavePolygon")
        self.assertEqual(mitcad["commands"][-1]["def"]["type"], "extrude")

    def test_parameterized_polygon_extrude_reuses_sketch_relations(self):
        width = Parameter("polygon_width", 20)
        with Sketch(name="Parameterized", plane="XY") as sketch:
            Polygon2D(
                [(0, 0), (0, 30), (width, 30), (width, 0)],
                plane="XY",
            )
        shape = sketch.extrude(10, sym=True)
        model = self.assert_solidcraft_compatibility(
            shape,
            "ParameterizedPolygon",
        )
        self.assertIsInstance(model.root, ExtrudeIR)

        relations = model.root.sketch.relations
        self.assertIsInstance(relations, SketchRelationsIR)
        self.assertEqual(
            [constraint.orientation for constraint in relations.constraints],
            ["vertical", "horizontal", "vertical", "horizontal"],
        )
        self.assertEqual(
            [dimension.line for dimension in relations.dimensions],
            [0, 1],
        )
        self.assertEqual(relations.dimensions[0].value, 30)
        self.assertIs(relations.dimensions[1].value, width)
        self.assertEqual(relations.coordinate_dimensions, ())

        mitcad = compile_mitcad_ir(model, "ParameterizedPolygon")
        sketch_def = mitcad["commands"][-2]["def"]
        self.assertEqual(
            [constraint["type"] for constraint in sketch_def["constraints"]],
            ["vertical", "horizontal", "vertical", "horizontal"],
        )
        self.assertEqual(
            [dimension["type"] for dimension in sketch_def["dimensions"]],
            ["length", "length"],
        )
        self.assertEqual(sketch_def["dimensions"][0]["value"], 30)
        self.assertEqual(sketch_def["dimensions"][1]["value"], "polygon_width")
        self.assertEqual(mitcad["commands"][-1]["def"]["type"], "extrude")

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
        self.assertIsNone(model.root.distance2)
        self.assertFalse(model.root.flip)

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

    def test_asymmetric_top_chamfer_is_typed_with_two_distances(self):
        primary = Parameter("primary_chamfer", 0.18)
        secondary = Parameter("secondary_chamfer", 0.65)
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            primary,
            distance2=secondary,
            edges=Edges.from_faces(Faces.TOP),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "AsymmetricChamfer",
        )
        self.assertIsInstance(model.root, ChamferIR)
        self.assertIsInstance(model.root.base, PlacementIR)
        self.assertIsInstance(model.root.base.primitive, BoxIR)
        self.assertIs(model.root.distance, primary)
        self.assertIs(model.root.distance2, secondary)
        self.assertFalse(model.root.flip)
        self.assertEqual(model.root.edges.faces, ("top",))
        self.assertEqual(
            model.parameters,
            (
                ParameterIR("primary_chamfer", 0.18, roles=("length",)),
                ParameterIR("secondary_chamfer", 0.65, roles=("length",)),
            ),
        )

        solidcraft = compile_solidcraft_ir(model, "AsymmetricChamfer")
        command = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.chamfer"
        )
        self.assertEqual(command["params"]["distance"], "primary_chamfer")
        self.assertEqual(command["params"]["distance2"], "secondary_chamfer")
        self.assertNotIn("flip", command["params"])

        mitcad = compile_mitcad_ir(model, "AsymmetricChamfer")
        stage = mitcad["replay"][0]
        boundary = stage["bind_face_boundary_edges"]
        self.assertEqual(boundary["face"]["normal"], [0, 0, 1])
        self.assertEqual(boundary["face_name"], "reference_face")
        chamfer = stage["commands"][0]["def"]
        self.assertEqual(chamfer["type"], "chamfer")
        self.assertEqual(
            chamfer["sets"][0]["size"],
            {
                "type": "two_distances",
                "distance1": "primary_chamfer",
                "distance2": "secondary_chamfer",
            },
        )
        self.assertEqual(
            chamfer["sets"][0]["reference_face"],
            {"$mitcad_bind": "reference_face"},
        )
        self.assertNotIn("flip", chamfer["sets"][0])

    def test_asymmetric_top_chamfer_preserves_flip(self):
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            0.18,
            distance2=0.65,
            flip=True,
            edges=Edges.from_faces(Faces.TOP),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "FlippedAsymmetricChamfer",
        )
        self.assertIsInstance(model.root, ChamferIR)
        self.assertTrue(model.root.flip)

        solidcraft = compile_solidcraft_ir(
            model,
            "FlippedAsymmetricChamfer",
        )
        command = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.chamfer"
        )
        self.assertTrue(command["params"]["flip"])

        mitcad = compile_mitcad_ir(
            model,
            "FlippedAsymmetricChamfer",
        )
        chamfer_set = mitcad["replay"][0]["commands"][0]["def"]["sets"][0]
        self.assertNotIn("distance2", chamfer_set)
        self.assertEqual(
            chamfer_set["reference_face"],
            {"$mitcad_bind": "reference_face"},
        )
        self.assertTrue(chamfer_set["flip"])
        self.assertEqual(
            chamfer_set["size"],
            {
                "type": "two_distances",
                "distance1": 0.18,
                "distance2": 0.65,
            },
        )

    def test_asymmetric_non_top_face_boundary_is_typed(self):
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            0.18,
            distance2=0.65,
            edges=Edges.from_faces(Faces.FRONT),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "AsymmetricFront",
        )
        self.assertIsInstance(model.root, ChamferIR)
        self.assertEqual(
            model.root.edges,
            FaceBoundaryIR(("front",)),
        )
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "AsymmetricFront")


    def test_plane_ir_rejects_non_principal_or_invalid_origins(self):
        for kwargs in (
            {"orientation": "ZX"},
            {"orientation": "XY", "origin": (0, 0)},
            {"orientation": "XY", "origin": (0, 0, True)},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PlaneIR(**kwargs)

    def test_shifted_sketch_plane_is_symbolic_semantic_ir_before_lowering(self):
        axis_x = Parameter("axis_x", 8)
        axis_z = Parameter("axis_z", 3)
        panel = Box(80, 46, 10)
        with Sketch(
            name="ShiftedPassThrough",
            plane="XY",
            offset=axis_z,
        ) as profile:
            Polygon2D(
                [
                    (12, -5),
                    (16, -5),
                    (16, 5),
                    (12, 5),
                ],
                plane="XY",
            )
        shape = panel - profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(axis_x, 0, axis_z),
            ),
        )

        model = normalize_shape(shape)

        self.assertIsInstance(model.root, RevolveIR)
        self.assertNotIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(model.root.operation, "cut")
        self.assertEqual(
            model.root.sketch.plane,
            PlaneIR(
                orientation="XY",
                origin=(0, 0, axis_z),
            ),
        )
        self.assertIs(model.root.sketch.plane.origin[2], axis_z)
        self.assertIs(model.root.axis.origin[2], axis_z)
        self.assertIs(model.root.axis.origin[0], axis_x)
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["axis_z", "axis_x"],
        )

    def test_parameterized_polygon_revolve_is_typed_for_both_backends(self):
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
        shape = sketch.revolve(axis=Axis.X, angle=sweep)

        model = self.assert_solidcraft_compatibility(shape, "NativeRevolve")
        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            model.root.axis,
            AxisLineIR(direction="X", origin=(0, 0, 0)),
        )
        self.assertIsNone(model.root.direction)
        self.assertEqual(model.root.region, RegionIR(outer=0))
        self.assertIsInstance(model.root.sketch.profiles[0], PolygonProfileIR)
        self.assertEqual(
            [
                (parameter.name, parameter.roles, parameter.unit)
                for parameter in model.parameters
            ],
            [
                ("radius", ("length",), "mm"),
                ("length", ("length",), "mm"),
                ("sweep", ("angle",), "deg"),
            ],
        )

        relations = model.root.sketch.relations
        self.assertEqual(
            relations,
            SketchRelationsIR(
                points=(
                    SketchPointIR((0, 0)),
                    SketchPointIR((0, radius)),
                    SketchPointIR((length, radius)),
                    SketchPointIR((length, 0)),
                ),
                lines=(
                    SketchLineIR(0, 1),
                    SketchLineIR(1, 2),
                    SketchLineIR(2, 3),
                    SketchLineIR(3, 0),
                ),
                constraints=(
                    SketchOrientationConstraintIR(0, "vertical"),
                    SketchOrientationConstraintIR(1, "horizontal"),
                    SketchOrientationConstraintIR(2, "vertical"),
                    SketchOrientationConstraintIR(3, "horizontal"),
                ),
                dimensions=(
                    SketchLengthDimensionIR(0, radius),
                    SketchLengthDimensionIR(1, length),
                ),
            ),
        )
        self.assertIs(relations.points[1].position[1], radius)
        self.assertIs(relations.points[2].position[0], length)
        self.assertIs(relations.dimensions[0].value, radius)
        self.assertIs(relations.dimensions[1].value, length)
        rendered = repr(relations).lower()
        for backend_identity in ("uid", "replay", "command", "p1", "c5", "k9"):
            self.assertNotIn(backend_identity, rendered)

        mitcad = compile_mitcad_ir(model, "NativeRevolve")
        sketch_def = mitcad["commands"][-2]["def"]
        revolve_def = mitcad["commands"][-1]["def"]
        self.assertEqual(sketch_def["type"], "sketch")
        self.assertEqual(sketch_def["plane"], "xz")
        self.assertEqual(
            [entity["type"] for entity in sketch_def["entities"]],
            [
                "point", "point", "point", "point",
                "line", "line", "line", "line",
            ],
        )
        self.assertEqual(
            [constraint["type"] for constraint in sketch_def["constraints"]],
            ["vertical", "horizontal", "vertical", "horizontal"],
        )
        self.assertEqual(
            [dimension["value"] for dimension in sketch_def["dimensions"]],
            ["radius", "length"],
        )
        self.assertEqual(revolve_def["type"], "revolve")
        self.assertEqual(
            revolve_def["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [5.0, 2.0]}],
        )
        self.assertEqual(revolve_def["axis"], "x")
        self.assertEqual(
            revolve_def["extent"],
            {"type": "angle", "angle": "sweep"},
        )
        self.assertEqual(revolve_def["operation"], "new_body")

    def test_sketch_relation_graph_rejects_missing_semantic_references(self):
        with self.assertRaisesRegex(ValueError, "missing semantic point"):
            SketchRelationsIR(
                points=(SketchPointIR((0, 0)),),
                lines=(SketchLineIR(0, 1),),
            )
        with self.assertRaisesRegex(ValueError, "missing semantic line"):
            SketchRelationsIR(
                points=(
                    SketchPointIR((0, 0)),
                    SketchPointIR((1, 0)),
                ),
                lines=(SketchLineIR(0, 1),),
                constraints=(
                    SketchOrientationConstraintIR(1, "horizontal"),
                ),
            )
        with self.assertRaisesRegex(ValueError, "coordinate dimension references"):
            SketchRelationsIR(
                points=(
                    SketchPointIR((0, 0)),
                    SketchPointIR((1, 0)),
                ),
                lines=(SketchLineIR(0, 1),),
                coordinate_dimensions=(
                    SketchCoordinateDimensionIR(2, "x", 1),
                ),
            )

    def test_non_rectangular_parameterized_revolve_has_coordinate_relations(self):
        width = Parameter("width", 10)
        height = Parameter("height", 4)
        half_width = width / 2
        crown = height + 1
        with Sketch(name="NonRectangle", plane="XZ") as sketch:
            Polygon2D(
                [
                    (0, 0),
                    (0, height),
                    (half_width, crown),
                    (width, 0),
                ],
                plane="XZ",
            )
        shape = sketch.revolve(axis=Axis.X)
        model = self.assert_solidcraft_compatibility(shape, "NonRectangle")
        self.assertIsInstance(model.root, RevolveIR)

        relations = model.root.sketch.relations
        self.assertIsInstance(relations, SketchRelationsIR)
        self.assertEqual(
            relations.lines,
            (
                SketchLineIR(0, 1),
                SketchLineIR(1, 2),
                SketchLineIR(2, 3),
                SketchLineIR(3, 0),
            ),
        )
        self.assertEqual(relations.constraints, ())
        self.assertEqual(relations.dimensions, ())
        self.assertEqual(
            [(dimension.point, dimension.axis) for dimension in relations.coordinate_dimensions],
            [
                (0, "x"), (0, "y"),
                (1, "x"), (1, "y"),
                (2, "x"), (2, "y"),
                (3, "x"), (3, "y"),
            ],
        )
        self.assertIs(relations.coordinate_dimensions[3].value, height)
        self.assertIs(relations.coordinate_dimensions[4].value, half_width)
        self.assertIs(relations.coordinate_dimensions[5].value, crown)
        self.assertIs(relations.coordinate_dimensions[6].value, width)

        rendered = repr(relations).lower()
        for backend_identity in ("uid", "replay", "command", "p1", "c6", "k10"):
            self.assertNotIn(backend_identity, rendered)

        mitcad = compile_mitcad_ir(model, "NonRectangle")
        sketch_def = mitcad["commands"][-2]["def"]
        self.assertEqual(
            [entity["type"] for entity in sketch_def["entities"]],
            [
                "point",
                "point", "point", "point", "point",
                "line", "line", "line", "line",
            ],
        )
        self.assertTrue(sketch_def["entities"][0]["fixed"])
        self.assertEqual(
            [dimension["type"] for dimension in sketch_def["dimensions"]],
            [
                "horizontal_distance", "vertical_distance",
                "horizontal_distance", "vertical_distance",
                "horizontal_distance", "vertical_distance",
                "horizontal_distance", "vertical_distance",
            ],
        )
        values = [dimension["value"] for dimension in sketch_def["dimensions"]]
        self.assertIn("height", values)
        self.assertIn("width", values)
        rendered_values = [str(value) for value in values]
        self.assertTrue(
            any("width" in value and "2" in value for value in rendered_values)
        )
        self.assertTrue(
            any("height" in value and "1" in value for value in rendered_values)
        )

    def test_shifted_axis_revolve_cut_is_one_semantic_feature(self):
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
        shape = panel - profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(axis_x, 0, 0),
            ),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "ShiftedRevolveCut",
        )
        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(model.root.operation, "cut")
        self.assertIsInstance(model.root.target, PlacementIR)
        self.assertEqual(
            model.root.axis,
            AxisLineIR(
                direction="Y",
                origin=(axis_x, 0, 0),
            ),
        )

        solidcraft = compile_solidcraft_ir(
            model,
            "ShiftedRevolveCut",
        )
        revolve = solidcraft["commands"][-1]
        self.assertEqual(revolve["command"], "solid.revolve")
        self.assertEqual(revolve["params"]["operation"], "cut")
        self.assertEqual(
            revolve["params"]["axis"],
            {
                "origin": ["axis_x", 0, 0],
                "dir": [0.0, 1.0, 0.0],
            },
        )
        self.assertEqual(revolve["params"]["targets"], ["ShiftedRevolveCut"])
        self.assertFalse(
            any(
                row["command"] in {
                    "solid.boolean",
                    "solid.cut",
                    "solid.subtract",
                }
                for row in solidcraft["commands"]
            )
        )

        mitcad = compile_mitcad_ir(
            model,
            "ShiftedRevolveCut",
        )
        self.assertEqual(
            [row["cmd"] for row in mitcad["commands"]],
            ["add_parameter", "add_feature"],
        )
        self.assertEqual(
            mitcad["replay"][0]["bind_single_body"],
            "body",
        )
        replay_commands = mitcad["replay"][0]["commands"]
        sketch_def = replay_commands[0]["def"]
        revolve_def = replay_commands[1]["def"]
        construction = [
            entity
            for entity in sketch_def["entities"]
            if entity.get("construction") is True
        ]
        self.assertEqual(len(construction), 1)
        self.assertEqual(construction[0]["type"], "line")
        self.assertIn(
            "axis_x",
            [dimension["value"] for dimension in sketch_def["dimensions"]],
        )
        self.assertEqual(
            revolve_def["axis"],
            {
                "sketch": {"ref": "sk.uid"},
                "curve": construction[0]["id"],
            },
        )
        self.assertEqual(revolve_def["operation"], "cut")
        self.assertEqual(
            revolve_def["participants"],
            [{"$mitcad_bind": "body"}],
        )

    def test_shifted_plane_revolve_cut_lowers_same_ir_to_both_backends(self):
        axis_x = Parameter("axis_x", 8)
        axis_z = Parameter("axis_z", 3)
        panel = Box(80, 46, 30)
        with Sketch(
            name="ShiftedPassThrough",
            plane="XY",
            offset=axis_z,
        ) as profile:
            Polygon2D(
                [
                    (12, -5),
                    (16, -5),
                    (16, 5),
                    (12, 5),
                ],
                plane="XY",
            )
        shape = panel - profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(axis_x, 0, axis_z),
            ),
        )

        model = self.assert_solidcraft_compatibility(
            shape,
            "ShiftedPlaneRevolveCut",
        )
        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            model.root.sketch.plane,
            PlaneIR(
                orientation="XY",
                origin=(0, 0, axis_z),
            ),
        )

        solidcraft = compile_solidcraft_ir(
            model,
            "ShiftedPlaneRevolveCut",
        )
        sketch_create = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "sketch.create"
        )
        self.assertEqual(
            sketch_create["params"],
            {
                "name": "ShiftedPassThrough",
                "plane": "XY",
                "offset": "axis_z",
            },
        )

        mitcad = compile_mitcad_ir(
            model,
            "ShiftedPlaneRevolveCut",
        )
        replay_commands = mitcad["replay"][0]["commands"]
        self.assertEqual(
            [row["def"]["type"] for row in replay_commands],
            ["construction_plane", "sketch", "revolve"],
        )
        plane_command, sketch_command, revolve_command = replay_commands
        self.assertEqual(
            plane_command["def"],
            {
                "type": "construction_plane",
                "definition": {
                    "type": "offset",
                    "plane": "xy",
                    "distance": "axis_z",
                },
            },
        )
        self.assertEqual(
            sketch_command["def"]["plane"],
            {"ref": "plane.uid"},
        )
        self.assertNotIn("plane", model.root.axis.__dict__)
        self.assertIn(
            "axis_x",
            [
                dimension["value"]
                for dimension in sketch_command["def"]["dimensions"]
            ],
        )
        self.assertEqual(revolve_command["def"]["operation"], "cut")
        self.assertEqual(
            revolve_command["def"]["participants"],
            [{"$mitcad_bind": "body"}],
        )

    def test_suppression_configuration_is_semantic_ir_before_lowering(self):
        axis_x = Parameter("axis_x", 8)
        axis_z = Parameter("axis_z", 3)
        panel = Box(40, 24, 20)
        with Sketch(
            name="Stepped pass through",
            plane="XY",
            offset=axis_z,
        ) as profile:
            Polygon2D(
                [
                    (axis_x, -12),
                    (axis_x + 2.25, -12),
                    (axis_x + 2.25, -9),
                    (axis_x + 1.85, -9),
                    (axis_x + 1.85, 9),
                    (axis_x + 2.25, 9),
                    (axis_x + 2.25, 12),
                    (axis_x, 12),
                ],
                plane="XY",
            )

        pass_through = profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(axis_x, 0, axis_z),
            ),
        )
        body = panel - pass_through
        configured = Configure(
            body,
            active="Cut",
            columns=(Suppress(pass_through),),
            rows={
                "Cut": (False,),
                "Suppressed": (True,),
            },
        )

        model = normalize_model(configured)

        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(model.root.operation, "cut")
        self.assertNotIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["axis_z", "axis_x"],
        )
        self.assertEqual(
            model.configuration,
            ConfigurationIR(
                active="Cut",
                columns=(
                    SuppressionColumnIR(
                        feature=FeatureRefIR(path=("root",)),
                    ),
                ),
                rows=(
                    ConfigurationRowIR(name="Cut", cells=(False,)),
                    ConfigurationRowIR(name="Suppressed", cells=(True,)),
                ),
            ),
        )
        self.assertNotIn("uid", repr(model.configuration).lower())
        self.assertNotIn("command", repr(model.configuration).lower())
        self.assertNotIn("replay", repr(model.configuration).lower())

        self.assertEqual(
            compile_solidcraft_ir(model, "ShiftedAxisRevolve"),
            _compile_model_with_dependencies(
                configured,
                "ShiftedAxisRevolve",
            )[0],
        )

    def test_boolean_feature_references_follow_semantic_history_roles(self):
        sphere = Sphere(20)
        extension = Box(30, 30, 20).move(x=18, z=10)
        joined = sphere + extension
        bore = Cylinder(d=8, h=60, axis=Axis.X)
        cut = joined - bore
        clip = Box(50, 50, 30).move(z=15)
        design = cut & clip

        configured_clip = Configure(
            design,
            active="Clipped",
            columns=(Suppress(clip),),
            rows={"Clipped": (False,), "Unclipped": (True,)},
        )
        clip_model = normalize_model(configured_clip)
        self.assertIsInstance(clip_model.root, BooleanIR)
        clip_ref = clip_model.configuration.columns[0].feature
        self.assertEqual(
            clip_ref,
            FeatureRefIR(path=("root", "tool")),
        )
        clip_node = resolve_feature_ref(clip_model.root, clip_ref)
        self.assertIsInstance(clip_node, PlacementIR)
        self.assertIsInstance(clip_node.primitive, BoxIR)

        configured_bore = Configure(
            design,
            active="Bored",
            columns=(Suppress(bore),),
            rows={"Bored": (False,), "Solid": (True,)},
        )
        bore_model = normalize_model(configured_bore)
        bore_ref = bore_model.configuration.columns[0].feature
        self.assertEqual(
            bore_ref,
            FeatureRefIR(path=("root", "target", "tool")),
        )
        bore_node = resolve_feature_ref(bore_model.root, bore_ref)
        self.assertIsInstance(bore_node, PlacementIR)
        self.assertIsInstance(bore_node.primitive, CylinderIR)

        for reference in (clip_ref, bore_ref):
            rendered = repr(reference).lower()
            self.assertNotIn("uid", rendered)
            self.assertNotIn("command", rendered)
            self.assertNotIn("replay", rendered)

        clip_solidcraft = compile_solidcraft_ir(
            clip_model,
            "PrimitiveCsgConfigured",
        )
        clip_legacy = _compile_model_with_dependencies(
            configured_clip,
            "PrimitiveCsgConfigured",
        )[0]
        self.assertEqual(clip_solidcraft, clip_legacy)
        bound_commands = [
            command
            for command in clip_solidcraft["commands"]
            if "$config_name_1" in command.get("bind", {})
        ]
        self.assertEqual(len(bound_commands), 1)
        self.assertEqual(bound_commands[0]["command"], "solid.box")
        self.assertEqual(
            bound_commands[0]["params"]["operation"],
            "intersect",
        )

        bore_solidcraft = compile_solidcraft_ir(
            bore_model,
            "PrimitiveCsgBoreConfigured",
        )
        bore_bound = [
            command
            for command in bore_solidcraft["commands"]
            if "$config_name_1" in command.get("bind", {})
        ]
        self.assertEqual(len(bore_bound), 1)
        self.assertEqual(bore_bound[0]["command"], "solid.cylinder")
        self.assertEqual(bore_bound[0]["params"]["operation"], "cut")

    def test_boolean_feature_reference_rejects_non_member_before_lowering(self):
        sphere = Sphere(20)
        extension = Box(30, 30, 20).move(x=18, z=10)
        bore = Cylinder(d=8, h=60, axis=Axis.X)
        clip = Box(50, 50, 30).move(z=15)
        design = ((sphere + extension) - bore) & clip
        unrelated = Box(2, 2, 2)

        configured = Configure(
            design,
            active="Clipped",
            columns=(Suppress(unrelated),),
            rows={"Clipped": (False,), "Unclipped": (True,)},
        )

        with self.assertRaisesRegex(
            ValueError,
            "not a member of the typed Boolean history",
        ):
            normalize_model(configured)

    def test_feature_ref_resolver_rejects_invalid_semantic_role(self):
        model = normalize_shape(
            (Sphere(20) + Box(30, 30, 20).move(x=18, z=10))
            & Box(50, 50, 30).move(z=15)
        )
        with self.assertRaisesRegex(ValueError, "not valid for"):
            resolve_feature_ref(
                model.root,
                FeatureRefIR(path=("root", "tool", "target")),
            )

    def test_suppression_reference_must_be_the_authored_root_feature(self):
        panel = Box(40, 24, 20)
        with Sketch(name="PassThrough", plane="XY") as profile:
            Polygon2D(
                [(8, -5), (10, -5), (10, 5), (8, 5)],
                plane="XY",
            )
        pass_through = profile.revolve(
            axis=AxisLine(Axis.Y, origin=(8, 0, 0)),
        )
        body = panel - pass_through
        unrelated = Box(2, 2, 2)
        configured = Configure(
            body,
            active="Cut",
            columns=(Suppress(unrelated),),
            rows={"Cut": (False,), "Suppressed": (True,)},
        )

        with self.assertRaisesRegex(
            ValueError,
            "not the authored root Revolve feature",
        ):
            normalize_model(configured)

    def test_configuration_ir_rejects_non_suppression_columns_and_rules(self):
        panel = Box(40, 24, 20)
        with Sketch(name="PassThrough", plane="XY") as profile:
            Polygon2D(
                [(8, -5), (10, -5), (10, 5), (8, 5)],
                plane="XY",
            )
        pass_through = profile.revolve(
            axis=AxisLine(Axis.Y, origin=(8, 0, 0)),
        )
        body = panel - pass_through

        configured = Configure(
            body,
            active="Cut",
            columns=(Suppress(pass_through),),
            rows={"Cut": (False,), "Suppressed": (True,)},
        )
        object.__setattr__(configured, "rules", ("unsupported",))
        with self.assertRaisesRegex(ValueError, "does not support configuration rules"):
            normalize_model(configured)

    def test_revolve_fixed_partial_angle_keeps_degree_semantics(self):
        with Sketch(name="HalfProfile", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 4), (10, 4), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=180))
        self.assertIsInstance(model.root, RevolveIR)
        definition = compile_mitcad_ir(
            model,
            "HalfRevolve",
        )["commands"][-1]["def"]
        self.assertEqual(
            definition["extent"],
            {"type": "angle", "angle": "180 deg"},
        )

    def test_simple_concave_polygon_revolve_is_typed(self):
        with Sketch(name="ConcaveRevolve", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, 5), (5, 2), (10, 5), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X))
        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            compile_mitcad_ir(model, "ConcaveRevolve")["commands"][-1]["def"]["type"],
            "revolve",
        )

    def test_mixed_role_revolve_parameter_is_typed_by_use_site(self):
        shared = Parameter("shared", 4)
        with Sketch(name="MixedRole", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, shared), (10, shared), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=shared))
        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            model.parameters,
            (
                ParameterIR(
                    "shared",
                    4,
                    roles=("length", "angle"),
                ),
            ),
        )
        self.assertEqual(model.parameters[0].unit, "")

        solidcraft = compile_solidcraft_ir(model, "MixedRoleRevolve")
        parameter = solidcraft["commands"][0]["params"]
        self.assertEqual(
            parameter,
            {
                "name": "shared",
                "expression": "4",
                "unit": "",
            },
        )
        line = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "sketch.line"
        )
        self.assertEqual(
            line["params"]["points"],
            [
                [0, 0],
                [0, "shared * 1 mm"],
                [10, "shared * 1 mm"],
                [10, 0],
            ],
        )
        revolve = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.revolve"
        )
        self.assertEqual(revolve["params"]["angle"], "shared * 1 deg")

        mitcad = compile_mitcad_ir(model, "MixedRoleRevolve")
        self.assertEqual(
            mitcad["commands"][0],
            {
                "cmd": "add_parameter",
                "name": "shared",
                "unit": "",
                "expression": "4",
            },
        )
        sketch_def = mitcad["commands"][-2]["def"]
        self.assertIn(
            "shared * 1 mm",
            [dimension["value"] for dimension in sketch_def["dimensions"]],
        )
        self.assertEqual(
            mitcad["commands"][-1]["def"]["extent"],
            {
                "type": "angle",
                "angle": "shared * 1 deg",
            },
        )

    def test_mixed_role_parameter_inside_affine_expression_is_typed(self):
        shared = Parameter("shared_expression", 4)
        height = shared + 1
        self.assertEqual(
            height.scalar_ir,
            ScalarBinaryIR(
                "add",
                ScalarParameterRefIR("shared_expression"),
                ScalarLiteralIR(1),
            ),
        )

        with Sketch(name="MixedRoleExpression", plane="XZ") as sketch:
            Polygon2D(
                [
                    (0, 0),
                    (0, height),
                    (10, height),
                    (10, 0),
                ],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=shared))

        self.assertIsInstance(model.root, RevolveIR)
        self.assertEqual(
            [(parameter.name, parameter.roles) for parameter in model.parameters],
            [("shared_expression", ("length", "angle"))],
        )

        solidcraft = compile_solidcraft_ir(model, "MixedRoleExpression")
        parameter = next(
            row["params"]
            for row in solidcraft["commands"]
            if row["command"] == "parameters.add"
        )
        self.assertEqual(
            parameter,
            {
                "name": "shared_expression",
                "expression": "4",
                "unit": "",
            },
        )
        line = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "sketch.line"
        )
        length_expression = "(shared_expression * 1 mm) + (1 mm)"
        self.assertEqual(
            line["params"]["points"],
            [
                [0, 0],
                [0, length_expression],
                [10, length_expression],
                [10, 0],
            ],
        )
        revolve = next(
            row
            for row in solidcraft["commands"]
            if row["command"] == "solid.revolve"
        )
        self.assertEqual(
            revolve["params"]["angle"],
            "shared_expression * 1 deg",
        )

        mitcad = compile_mitcad_ir(model, "MixedRoleExpression")
        self.assertEqual(
            mitcad["commands"][0],
            {
                "cmd": "add_parameter",
                "name": "shared_expression",
                "unit": "",
                "expression": "4",
            },
        )
        sketch_def = mitcad["commands"][-2]["def"]
        self.assertIn(
            length_expression,
            [dimension["value"] for dimension in sketch_def["dimensions"]],
        )
        self.assertEqual(
            mitcad["commands"][-1]["def"]["extent"],
            {
                "type": "angle",
                "angle": "shared_expression * 1 deg",
            },
        )

    def test_text_only_mixed_role_expression_remains_legacy(self):
        shared = Parameter("text_only_shared", 4)
        height = Expression(5, "text_only_shared + 1 mm", (shared,))
        with Sketch(name="TextOnlyMixedRole", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, height), (10, height), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=shared))
        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "TextOnlyMixedRole")

    def test_derived_unit_mixed_role_expression_is_typed_but_backends_fail_closed(self):
        shared = Parameter("derived_shared", 4)
        factor = Parameter("derived_factor", 2)
        height = shared * factor
        with Sketch(name="DerivedMixedRole", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, height), (10, height), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=shared))
        self.assertIsInstance(model.root, RevolveIR)
        self.assertIsNotNone(height.scalar_ir)
        with self.assertRaises(ModelError):
            compile_solidcraft_ir(model, "DerivedMixedRole")
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "DerivedMixedRole")

    def test_cone_is_generic_geometry_plus_placement_ir(self):
        shape = Cone(d=10, h=20)

        model = self.assert_solidcraft_compatibility(shape, "ConeTest")
        self.assertIsInstance(model.root, PlacementIR)
        self.assertIsInstance(model.root.primitive, ConeIR)
        self.assertEqual(model.root.primitive.height, 20)
        self.assertEqual(model.root.primitive.diameter, 10)
        self.assertEqual(model.root.primitive.top_diameter, 0)
        self.assertEqual(model.root.primitive.axis, "Z")
        self.assertEqual(model.root.point, (0, 0, 0))
        self.assertEqual(model.root.anchor, (0, 0, 0))

        mitcad = compile_mitcad_ir(model, "ConeTest")
        cone = mitcad["commands"][-1]["def"]
        self.assertEqual(cone["type"], "cone")
        self.assertEqual(cone["center"], [0, 0])
        self.assertEqual(cone["radius"], 5.0)
        self.assertEqual(cone["top_radius"], 0.0)
        self.assertEqual(cone["height"], 20)
        self.assertFalse(cone["symmetric"])
        plane = mitcad["commands"][-2]
        self.assertEqual(plane["def"]["type"], "construction_plane")
        self.assertEqual(plane["def"]["definition"]["plane"], "xy")
        self.assertEqual(plane["def"]["definition"]["distance"], -10.0)

    def test_parameterized_bottom_frustum_preserves_typed_dimensions(self):
        height = Parameter("cone_height", 8)
        diameter = Parameter("cone_diameter", 18)
        top = Parameter("cone_top_diameter", 10)
        shape = Cone(
            d=diameter,
            top_d=top,
            h=height,
            anchor=Anchor.BOTTOM,
        )

        model = self.assert_solidcraft_compatibility(shape, "Frustum")
        self.assertEqual(
            [parameter.name for parameter in model.parameters],
            ["cone_height", "cone_diameter", "cone_top_diameter"],
        )
        self.assertIsInstance(model.root.primitive, ConeIR)
        self.assertEqual(model.root.anchor, (0, 0, -1))

        mitcad = compile_mitcad_ir(model, "Frustum")
        cone = mitcad["commands"][-1]["def"]
        self.assertEqual(cone["plane"], "xy")
        self.assertIn("cone_diameter", str(cone["radius"]))
        self.assertIn("cone_top_diameter", str(cone["top_radius"]))
        self.assertEqual(cone["height"], "cone_height")

    def test_placed_bottom_frustum_uses_backend_owned_offset_plane(self):
        shape = Cone(
            d=18,
            top_d=10,
            h=8,
            anchor=Anchor.BOTTOM,
        ).at(
            0,
            0,
            18,
            anchor=Anchor.BOTTOM,
        )

        model = self.assert_solidcraft_compatibility(shape, "PlacedFrustum")
        self.assertIsInstance(model.root.primitive, ConeIR)
        self.assertEqual(model.root.point, (0, 0, 18))
        self.assertEqual(model.root.anchor, (0, 0, -1))
        self.assertTrue(model.root.explicit)

        mitcad = compile_mitcad_ir(model, "PlacedFrustum")
        self.assertEqual(len(mitcad["commands"]), 2)
        plane, feature = mitcad["commands"]
        self.assertEqual(plane["def"]["type"], "construction_plane")
        self.assertEqual(plane["def"]["definition"]["plane"], "xy")
        self.assertEqual(plane["def"]["definition"]["distance"], 18)
        self.assertEqual(feature["def"]["plane"], {"ref": "cone_plane.uid"})
        self.assertEqual(feature["def"]["center"], [0, 0])
        self.assertEqual(feature["def"]["radius"], 9.0)
        self.assertEqual(feature["def"]["top_radius"], 5.0)

    def test_x_axis_cone_uses_principal_yz_plane(self):
        shape = Cone(
            d=12,
            top_d=4,
            h=20,
            axis=Axis.X,
            anchor=Anchor.LEFT,
        )

        model = self.assert_solidcraft_compatibility(shape, "XAxisCone")
        self.assertEqual(model.root.primitive.axis, "X")
        self.assertEqual(model.root.anchor, (-1, 0, 0))

        cone = compile_mitcad_ir(model, "XAxisCone")["commands"][-1]["def"]
        self.assertEqual(cone["plane"], "yz")
        self.assertEqual(cone["center"], [0, 0])
        self.assertEqual(cone["height"], 20)


if __name__ == "__main__":
    unittest.main()
