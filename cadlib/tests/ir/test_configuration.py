from ._support import *

class ConfigurationIRTests(SemanticIRTestCase):
    def test_named_feature_identity_and_initial_state_are_semantic(self):
        body = Box(30, 30, 10, anchor=Anchor.BOTTOM)
        cutter = Cylinder(d=6, h=12)
        with feature("service_bore", suppressed=True) as service_bore:
            body = body - cutter

        model = normalize_model(body)

        self.assertEqual(len(model.named_features), 1)
        named = model.named_features[0]
        self.assertIsInstance(named, NamedFeatureIR)
        self.assertEqual(named.name, "service_bore")
        self.assertTrue(named.suppressed)
        self.assertEqual(named.feature, FeatureRefIR(path=("root",)))

        solidcraft = compile_solidcraft_ir(model, "NamedFeature")
        suppress = [
            command
            for command in solidcraft["commands"]
            if command["command"] == "timeline.suppress"
        ]
        self.assertEqual(len(suppress), 1)

        configured = body.configure(
            active="Installed",
            columns=(service_bore,),
            rows={
                "Installed": (False,),
                "Removed": (True,),
            },
        )
        configured_model = normalize_model(configured)
        self.assertEqual(
            configured_model.configuration.columns[0].feature,
            FeatureRefIR(path=("root",)),
        )

        with self.assertRaisesRegex(
            ModelError,
            "initially suppressed named features",
        ):
            compile_mitcad_ir(model, "NamedFeature")

    def test_shifted_sphere_configuration_binds_semantic_feature_not_helper(self):
        sphere = Sphere(5).move(z=15)
        body = Box(30, 30, 30, anchor=Anchor.BOTTOM) - sphere
        configured = body.configure(
            active="Cut",
            columns=(sphere,),
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
        configured = body.configure(
            active="Cut",
            columns=(cone,),
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

    def test_translation_feature_ref_descends_into_boolean_body_semantics(self):
        base = Box(30, 20, 10)
        bore = Cylinder(d=6, h=14)
        design = (base - bore).move(x=10)
        configured = design.configure(
            active="Cut",
            columns=(bore,),
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

    def test_boolean_feature_ref_recurses_through_typed_tool_history(self):
        base = Box(30, 30, 10)
        first = Cylinder(d=6, h=12)
        second = Cylinder(d=4, h=12).move(x=8)
        tool = first + second
        design = base - tool

        configured = design.configure(
            active="Cut",
            columns=(second,),
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
        configured = body.configure(
            active="Cut",
            columns=(pass_through,),
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

        configured_clip = design.configure(
            active="Clipped",
            columns=(clip,),
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

        bore_design = type(design)(design.kind, design.data)
        configured_bore = bore_design.configure(
            active="Bored",
            columns=(bore,),
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

        configured = design.configure(
            active="Clipped",
            columns=(unrelated,),
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
        configured = body.configure(
            active="Cut",
            columns=(unrelated,),
            rows={"Cut": (False,), "Suppressed": (True,)},
        )

        with self.assertRaisesRegex(
            ValueError,
            "not the authored root Revolve feature",
        ):
            normalize_model(configured)

    def test_configuration_ir_has_no_retired_rule_surface(self):
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
        configured = body.configure(
            active="Cut",
            columns=(pass_through,),
            rows={"Cut": (False,), "Suppressed": (True,)},
        )

        model = normalize_model(configured)

        self.assertFalse(hasattr(model.configuration, "rules"))

