from ._support import *

class SketchIRTests(SemanticIRTestCase):
    def test_symbolic_explicit_sketch_origin_keeps_semantic_ir_and_stable_lowering(self):
        frame_x = Parameter("frame_x", 12)
        with Sketch(
            name="RotatedTool",
            plane="XY",
            origin=(frame_x, 3, 0),
            rotation=(0, 0, 45),
        ) as tool_profile:
            Polygon2D([(0, 0), (6, 0), (0, 6)])

        shape = Box(30, 30, 10) - tool_profile.extrude(8)
        model = self.assert_solidcraft_compatibility(
            shape,
            "SymbolicRotatedTool",
        )

        self.assertIsInstance(model.root, BooleanIR)
        self.assertIsInstance(model.root.tool, ExtrudeIR)
        self.assertEqual(
            {parameter.name for parameter in model.parameters},
            {"frame_x"},
        )
        self.assertEqual(
            model.root.tool.sketch.plane.origin[0],
            frame_x,
        )

        solidcraft = compile_solidcraft_ir(model, "SymbolicRotatedTool")
        rotated = next(
            command
            for command in solidcraft["commands"]
            if (
                command["command"] == "sketch.create"
                and command["params"]["name"] == "RotatedTool"
            )
        )
        self.assertEqual(
            rotated["params"]["plane"]["origin"],
            [12.0, 3.0, 0.0],
        )

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

