"""Frontend ownership and compatibility-facade contracts."""

import unittest

import scpf
import scpf.core as core


class FrontendDomainOwnershipTests(unittest.TestCase):
    def test_representative_authoring_objects_have_domain_owners(self):
        self.assertEqual(
            core.Parameter.__module__,
            "scpf.frontend.scalars",
        )
        self.assertEqual(
            core.Anchor.__module__,
            "scpf.frontend.selectors",
        )
        self.assertEqual(
            core.Shape.__module__,
            "scpf.frontend.shape",
        )
        self.assertEqual(
            core.Rectangle2D.__module__,
            "scpf.frontend.profiles",
        )
        self.assertEqual(
            core.Box.__module__,
            "scpf.frontend.primitives",
        )
        self.assertEqual(
            core.Hole.__module__,
            "scpf.frontend.features",
        )

    def test_public_scpf_and_core_facades_export_same_objects(self):
        names = (
            "Parameter",
            "Anchor",
            "Axis",
            "AxisLine",
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

    def test_private_core_compatibility_names_still_resolve_to_domain_owners(self):
        self.assertEqual(
            core._pv.__module__,
            "scpf.frontend.scalars",
        )
        self.assertEqual(
            core._direction_selector.__module__,
            "scpf.frontend.selectors",
        )
        self.assertEqual(
            core._shape.__module__,
            "scpf.frontend.shape",
        )
        self.assertEqual(
            core._box_corner_from_anchor.__module__,
            "scpf.frontend.primitives",
        )
        self.assertEqual(
            core._hole_spec.__module__,
            "scpf.frontend.features",
        )


if __name__ == "__main__":
    unittest.main()
