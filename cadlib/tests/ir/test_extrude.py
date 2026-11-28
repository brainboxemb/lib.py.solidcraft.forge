from ._support import *

class ExtrudeIRTests(SemanticIRTestCase):
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

