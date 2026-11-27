"""Contracts for the engine-neutral Forge semantic IR boundary."""
import unittest

from scpf import (
    Anchor,
    Axis,
    AxisLine,
    Box,
    Circle2D,
    Configure,
    Cone,
    Cylinder,
    Edges,
    Faces,
    Parameter,
    Polygon2D,
    Sketch,
    Sphere,
    Suppress,
)
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.compiler import (
    ModelError,
    _compile_model_with_dependencies,
    _compile_shape_legacy_with_dependencies,
)
from scpf.ir import (
    AxisLineIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    CylinderIR,
    ExtrudeIR,
    FeatureRefIR,
    ConfigurationIR,
    ConfigurationRowIR,
    SuppressionColumnIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    SketchIR,
    SketchCoordinateDimensionIR,
    SketchLengthDimensionIR,
    SketchLineIR,
    SketchOrientationConstraintIR,
    SketchPointIR,
    SketchRelationsIR,
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

    def test_unqualified_sphere_placement_stays_legacy_and_mitcad_fails_closed(self):
        for shape in (
            Sphere(20, anchor=Anchor.TOP),
            Sphere(20).move(z=10),
        ):
            model = normalize_shape(shape)
            self.assertIsInstance(model.root, LegacyShapeIR)
            with self.assertRaises(ModelError):
                compile_mitcad_ir(model, "UnsupportedSphere")

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
        )

        for model in cases:
            for compiler in (compile_solidcraft_ir, compile_mitcad_ir):
                with self.subTest(model=model.root.sketch.name, compiler=compiler):
                    with self.assertRaises(ModelError):
                        compiler(model, model.root.sketch.name)

    def test_three_profile_exact_region_stays_legacy_for_solidcraft_only(self):
        with Sketch(name="Three circles", plane="XY") as sketch:
            Circle2D(d=10)
            Circle2D(d=8)
            Circle2D(d=6)
        shape = sketch.extrude(
            20,
            profiles=[(4.5, 0)],
            exact_regions=True,
        )

        model = normalize_shape(shape)
        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(
            compile_solidcraft_ir(model, "ThreeCircles"),
            _compile_shape_legacy_with_dependencies(
                shape,
                "ThreeCircles",
            )[0],
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'sketch_base_extrusion'",
        ):
            compile_mitcad_ir(model, "ThreeCircles")

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

    def test_parameterized_polygon_extrude_stays_legacy_until_qualified(self):
        width = Parameter("polygon_width", 20)
        with Sketch(name="Parameterized", plane="XY") as sketch:
            Polygon2D(
                [(0, 0), (width, 0), (width, 30), (0, 30)],
                plane="XY",
            )
        shape = sketch.extrude(10, sym=True)
        model = normalize_shape(shape)
        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(
            compile_solidcraft_ir(model, "LegacyPolygon"),
            _compile_shape_legacy_with_dependencies(
                shape,
                "LegacyPolygon",
            )[0],
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind "
            "'sketch_base_extrusion'",
        ):
            compile_mitcad_ir(model, "LegacyPolygon")

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

    def test_asymmetric_chamfer_stays_solidcraft_legacy_until_portable(self):
        shape = Box(
            60,
            40,
            12,
            anchor=Anchor.BOTTOM,
        ).chamfer(
            0.18,
            distance2=0.65,
            edges=Edges.from_faces(Faces.TOP),
        )

        model = normalize_shape(shape)
        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(model.root.source_kind, "chamfer")
        self.assertEqual(
            compile_solidcraft_ir(model, "AsymmetricChamfer"),
            _compile_shape_legacy_with_dependencies(
                shape,
                "AsymmetricChamfer",
            )[0],
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'chamfer'",
        ):
            compile_mitcad_ir(model, "AsymmetricChamfer")


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
            [(parameter.name, parameter.unit) for parameter in model.parameters],
            [
                ("radius", "mm"),
                ("length", "mm"),
                ("sweep", "deg"),
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
        self.assertTrue(any("width" in value and "2" in value for value in values))
        self.assertTrue(any("height" in value and "1" in value for value in values))

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

    def test_mixed_role_revolve_parameter_remains_legacy(self):
        shared = Parameter("shared", 4)
        with Sketch(name="MixedRole", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, shared), (10, shared), (10, 0)],
                plane="XZ",
            )
        model = normalize_shape(sketch.revolve(axis=Axis.X, angle=shared))
        self.assertIsInstance(model.root, LegacyShapeIR)
        with self.assertRaises(ModelError):
            compile_mitcad_ir(model, "UnsupportedRevolve")

    def test_unmigrated_surface_is_explicit_legacy_ir_only_for_solidcraft(self):
        shape = Cone(d=10, h=20)
        model = normalize_shape(shape)

        self.assertIsInstance(model.root, LegacyShapeIR)
        self.assertEqual(model.root.source_kind, "cone")
        solidcraft = compile_solidcraft_ir(model, "ConeTest")
        self.assertEqual(
            solidcraft["commands"][-1]["command"],
            "solid.cone",
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'cone'",
        ):
            compile_mitcad_ir(model, "ConeTest")


if __name__ == "__main__":
    unittest.main()
