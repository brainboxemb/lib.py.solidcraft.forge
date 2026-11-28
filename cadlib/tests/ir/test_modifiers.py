from ._support import *

class ModifierIRTests(SemanticIRTestCase):
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

        history_shape = body.fillet(
            0.5,
            edges=Edges.from_vertices("tip"),
        ).chamfer(
            0.25,
            edges=Edges.from_profile("far"),
        )
        history_model = self.assert_solidcraft_compatibility(
            history_shape,
            "ProfileHistoryChamfer",
        )
        self.assertIsInstance(history_model.root, ChamferIR)
        self.assertIsInstance(history_model.root.base, FilletIR)
        self.assertIsInstance(history_model.root.base.base, ExtrudeIR)
        self.assertEqual(
            history_model.root.edges,
            ProfileEdgeSetIR(
                patterns=("far",),
                kind="segments",
                sides="both",
            ),
        )

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

