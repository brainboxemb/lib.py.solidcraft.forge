"""Geometry-reference checks must reject correct envelopes with wrong internals."""

import math
import unittest


from qualification.geometry_contracts import geometry_contract


class GeometryContractTests(unittest.TestCase):
    def test_feature_cases_have_independent_geometry_contracts(self):
        for slug in ("anchored-holes", "rectangular-pattern", "slot-family"):
            with self.subTest(case=slug):
                contract = geometry_contract(slug)
                self.assertIsNotNone(contract)
                self.assertIn("volume_mm3", contract)
                self.assertTrue(contract["surface_distance_probes"])

    def test_solid_plate_cannot_match_anchored_holes_volume(self):
        contract = geometry_contract("anchored-holes")
        solid_plate_volume = 100.0 * 60.0 * 10.0
        self.assertGreater(
            abs(solid_plate_volume - contract["volume_mm3"]),
            contract["volume_tolerance_mm3"],
        )

    def test_volume_tolerance_still_rejects_a_missing_pattern_slot(self):
        contract = geometry_contract("rectangular-pattern")
        one_slot_volume = (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
        self.assertGreater(
            one_slot_volume,
            contract["volume_tolerance_mm3"],
        )

    def test_volume_tolerance_still_rejects_a_missing_slot_family_cut(self):
        contract = geometry_contract("slot-family")
        smallest_straight_slot_volume = (
            20.0 * 8.0 + math.pi * 4.0**2
        ) * 5.0
        self.assertGreater(
            smallest_straight_slot_volume,
            contract["volume_tolerance_mm3"],
        )

    def test_surface_probes_are_3d_not_front_view_only(self):
        contract = geometry_contract("anchored-holes")
        z_values = {
            round(probe["point"][2], 6)
            for probe in contract["surface_distance_probes"]
        }
        self.assertEqual(z_values, {1.0, 5.0, 9.0})


if __name__ == "__main__":
    unittest.main()
