"""Typed frontend primitive object contracts."""

import unittest
from dataclasses import FrozenInstanceError

from scpf import Anchor, Axis, Box, Cone, Cylinder, Shape, Sphere
from scpf.core import _direction_selector, _shape_center
from scpf.frontend.primitives import (
    Primitive,
    BoxPrimitive,
    SpherePrimitive,
    CylinderPrimitive,
    ConePrimitive,
)
from scpf.ir import (
    BoxIR,
    ConeIR,
    CylinderIR,
    PlacementIR,
    SphereIR,
    normalize_shape,
)


class TypedPrimitiveFrontendTests(unittest.TestCase):
    def test_public_factories_return_typed_shape_objects(self):
        box = Box(80, 50, 12, anchor=Anchor.BOTTOM)
        sphere = Sphere(6, anchor=Anchor.TOP)
        cylinder = Cylinder(d=8, h=20, axis=Axis.X, anchor=Anchor.LEFT)
        cone = Cone(d=12, top_d=8, h=16, axis=Axis.Y, anchor=Anchor.FRONT)

        for value in (box, sphere, cylinder, cone):
            self.assertIsInstance(value, Primitive)
            self.assertIsInstance(value, Shape)

        self.assertIsInstance(box, BoxPrimitive)
        self.assertEqual((box.length, box.width, box.thickness), (80, 50, 12))
        self.assertEqual(box.anchor.vector, (0, 0, -1))

        self.assertIsInstance(sphere, SpherePrimitive)
        self.assertEqual(sphere.radius, 6)

        self.assertIsInstance(cylinder, CylinderPrimitive)
        self.assertEqual(cylinder.diameter, 8)
        self.assertEqual(cylinder.height, 20)
        self.assertIs(cylinder.axis, Axis.X)

        self.assertIsInstance(cone, ConePrimitive)
        self.assertEqual(cone.diameter, 12)
        self.assertEqual(cone.top_diameter, 8)
        self.assertEqual(cone.height, 16)
        self.assertIs(cone.axis, Axis.Y)

    def test_kind_data_remain_legacy_compatibility_snapshots(self):
        box = Box(10, 20, 30, anchor=Anchor.BOTTOM)
        self.assertEqual(box.kind, "box")
        self.assertEqual(
            box.data,
            (10, 20, 30, box.anchor),
        )

        cylinder = Cylinder(d=8, h=15, axis=Axis.Y, anchor=Anchor.FRONT)
        self.assertEqual(
            cylinder.data,
            (15, 8, "Y", cylinder.anchor),
        )

    def test_typed_primitive_state_is_immutable(self):
        box = Box(10, 20, 30)
        with self.assertRaises(FrozenInstanceError):
            box.length = 99

    def test_alignment_center_dispatches_to_primitive_objects(self):
        self.assertEqual(
            _shape_center(Box(10, 20, 30, anchor=Anchor.BOTTOM)),
            (0, 0, 15),
        )
        self.assertEqual(
            _shape_center(Sphere(5, anchor=Anchor.RIGHT)),
            (-5, 0, 0),
        )
        self.assertEqual(
            _shape_center(Cylinder(d=8, h=20, axis=Axis.X, anchor=Anchor.LEFT)),
            (10, 0, 0),
        )
        self.assertEqual(
            _shape_center(Cone(d=12, top_d=8, h=20, anchor=Anchor.BOTTOM)),
            (0, 0, 10),
        )

    def test_absolute_placement_keeps_typed_primitive_children(self):
        box = Box(10, 20, 30).at(1, 2, 3, anchor=Anchor.BOTTOM)
        self.assertEqual(box.kind, "placed_box")
        self.assertIsInstance(box.data[0], BoxPrimitive)

        cylinder = Cylinder(d=8, h=20).at(1, 2, 3, anchor=Anchor.BOTTOM)
        self.assertEqual(cylinder.kind, "placed3d")
        self.assertIsInstance(cylinder.data[0], CylinderPrimitive)
        self.assertEqual(cylinder.data[0].anchor.vector, (0, 0, -1))

        cone = Cone(d=12, top_d=8, h=20).at(1, 2, 3, anchor=Anchor.TOP)
        self.assertEqual(cone.kind, "placed3d")
        self.assertIsInstance(cone.data[0], ConePrimitive)

        sphere = Sphere(5).at(1, 2, 3, anchor=Anchor.RIGHT)
        self.assertEqual(sphere.kind, "translated")
        self.assertIsInstance(sphere.data[0], SpherePrimitive)

    def test_semantic_ir_normalization_consumes_typed_primitives(self):
        cases = (
            (Box(10, 20, 30), BoxIR),
            (Sphere(5), SphereIR),
            (Cylinder(d=8, h=20, axis=Axis.Y), CylinderIR),
            (Cone(d=12, top_d=8, h=20, axis=Axis.X), ConeIR),
        )
        for shape, expected in cases:
            with self.subTest(shape=shape.kind):
                root = normalize_shape(shape).root
                self.assertIsInstance(root, PlacementIR)
                self.assertIsInstance(root.primitive, expected)

    def test_raw_tagged_shape_still_normalizes_as_legacy_compatibility(self):
        legacy = Shape(
            "box",
            (10, 20, 30, _direction_selector(Anchor.CENTER)),
        )
        root = normalize_shape(legacy).root
        self.assertIsInstance(root, PlacementIR)
        self.assertIsInstance(root.primitive, BoxIR)


if __name__ == "__main__":
    unittest.main()
