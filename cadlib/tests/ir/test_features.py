from ._support import *

class FeatureIRTests(SemanticIRTestCase):
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

