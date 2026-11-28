from ._support import *

class RevolveIRTests(SemanticIRTestCase):
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

