"""Frontend ownership and compatibility-facade contracts."""

import inspect
import unittest

import scpf
import scpf.core as core
from scpf.frontend import features, primitives, profiles, scalars, selectors, shape


class FrontendDomainOwnershipTests(unittest.TestCase):
    def test_representative_authoring_objects_have_domain_owners(self):
        expected = {
            selectors.Anchor: "scpf.frontend.selectors",
            selectors.AxisLine: "scpf.frontend.selectors",
            scalars.Parameter: "scpf.frontend.scalars",
            scalars.Expression: "scpf.frontend.scalars",
            shape.Shape: "scpf.frontend.shape",
            shape.feature: "scpf.frontend.shape",
            profiles.Rectangle2D: "scpf.frontend.profiles",
            primitives.Box: "scpf.frontend.primitives",
            primitives.Primitive: "scpf.frontend.primitives",
            primitives.BoxPrimitive: "scpf.frontend.primitives",
            features.Hole: "scpf.frontend.features",
        }
        for implementation, module in expected.items():
            with self.subTest(implementation=implementation):
                self.assertEqual(implementation.__module__, module)

    def test_public_scpf_and_core_facades_export_same_objects(self):
        names = (
            "Parameter",
            "Anchor",
            "Axis",
            "AxisLine",
            "Edges",
            "Shape",
            "Rectangle2D",
            "RoundedRectangle2D",
            "Box",
            "Cylinder",
            "Cone",
            "Hole",
            "CounterboreHole",
            "feature",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIs(getattr(scpf, name), getattr(core, name))

    def test_private_core_compatibility_names_point_to_domain_owners(self):
        expected = {
            "_pv": scalars._pv,
            "_dim_add": scalars._dim_add,
            "_native_dependencies": scalars._native_dependencies,
            "_direction_selector": selectors._direction_selector,
            "_feature_edge_selection": selectors._feature_edge_selection,
            "_shape": shape._shape,
            "_box_corner_from_anchor": primitives._box_corner_from_anchor,
            "_hole_spec": features._hole_spec,
        }
        for name, implementation in expected.items():
            with self.subTest(name=name):
                self.assertIs(getattr(core, name), implementation)

    def test_core_defines_no_frontend_implementation_objects(self):
        owned = {
            name
            for name, value in vars(core).items()
            if (
                inspect.isclass(value) or inspect.isfunction(value)
            )
            and getattr(value, "__module__", None) == "scpf.core"
        }
        self.assertEqual(owned, set())


if __name__ == "__main__":
    unittest.main()
