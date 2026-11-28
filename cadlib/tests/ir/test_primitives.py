from ._support import *

class PrimitiveIRTests(SemanticIRTestCase):
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

    def test_plane_ir_rejects_non_principal_or_invalid_origins(self):
        for kwargs in (
            {"orientation": "ZX"},
            {"orientation": "XY", "origin": (0, 0)},
            {"orientation": "XY", "origin": (0, 0, True)},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PlaneIR(**kwargs)

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

