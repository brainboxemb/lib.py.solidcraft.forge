from ._support import *

class BooleanIRTests(SemanticIRTestCase):
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

