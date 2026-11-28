"""Frontend ownership and compatibility-facade contracts."""

import inspect
import unittest

import scpf
import scpf.core as core
from scpf.frontend import features, primitives, profiles, scalars, selectors, shape


class FrontendOwnershipTests(unittest.TestCase):
    def test_public_and_core_facades_preserve_object_identity(self):
        public = {
            "Anchor": selectors.Anchor,
            "Axis": selectors.Axis,
            "Edges": selectors.Edges,
            "Parameter": scalars.Parameter,
            "Shape": shape.Shape,
            "feature": shape.feature,
            "Rectangle2D": profiles.Rectangle2D,
            "Box": primitives.Box,
            "Hole": features.Hole,
        }
        for name, implementation in public.items():
            with self.subTest(name=name):
                self.assertIs(getattr(core, name), implementation)
                self.assertIs(getattr(scpf, name), implementation)

    def test_private_core_compatibility_names_point_to_domain_owners(self):
        private = {
            "_direction_selector": selectors._direction_selector,
            "_feature_edge_selection": selectors._feature_edge_selection,
            "_dim_add": scalars._dim_add,
            "_native_dependencies": scalars._native_dependencies,
            "_shape": shape._shape,
            "_box_corner_from_anchor": primitives._box_corner_from_anchor,
            "_hole_spec": features._hole_spec,
        }
        for name, implementation in private.items():
            with self.subTest(name=name):
                self.assertIs(getattr(core, name), implementation)

    def test_representative_implementations_are_owned_by_frontend_domains(self):
        expected = {
            selectors.Anchor: "scpf.frontend.selectors",
            selectors.AxisLine: "scpf.frontend.selectors",
            scalars.Parameter: "scpf.frontend.scalars",
            scalars.Expression: "scpf.frontend.scalars",
            shape.Shape: "scpf.frontend.shape",
            shape.feature: "scpf.frontend.shape",
            profiles.Rectangle2D: "scpf.frontend.profiles",
            primitives.Box: "scpf.frontend.primitives",
            features.Hole: "scpf.frontend.features",
        }
        for implementation, module in expected.items():
            with self.subTest(implementation=implementation):
                self.assertEqual(implementation.__module__, module)

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
