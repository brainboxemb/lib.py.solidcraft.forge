from ._support import *

class OperationIRTests(SemanticIRTestCase):
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

    def test_move_of_unsupported_feature_body_remains_visible_legacy_boundary(self):
        with Sketch(name="MovedExtrude", plane="XY") as sketch:
            Rectangle2D(20, 10)
        shape = sketch.extrude(5).move(x=10)

        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "MovedExtrude")

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

