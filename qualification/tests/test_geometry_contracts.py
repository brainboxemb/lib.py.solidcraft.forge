"""Every qualification case must have one shared proof contract."""

import math
import unittest

from qualification.cases import QUALIFICATION_CASES
from qualification.geometry_contracts import geometry_contract, proof_contract


class GeometryContractTests(unittest.TestCase):
    def test_every_case_has_complete_shared_contract(self):
        for case in QUALIFICATION_CASES:
            slug = case["slug"]
            with self.subTest(case=slug):
                contract = geometry_contract(slug)
                self.assertTrue(contract["bounds"])
                self.assertTrue(contract["visual_boxes"])
                self.assertIsInstance(contract["bounds_sufficient"], bool)
                self.assertTrue(contract["bounds_reason"].strip())

    def test_non_bounds_cases_require_detailed_geometry_checks(self):
        for case in QUALIFICATION_CASES:
            slug = case["slug"]
            contract = geometry_contract(slug)
            if contract["bounds_sufficient"]:
                continue
            with self.subTest(case=slug):
                self.assertTrue(
                    "volume_mm3" in contract
                    or bool(contract.get("surface_distance_probes")),
                    f"{slug} says bounds are insufficient but declares no stronger check",
                )

    def test_proof_contract_separates_geometry_from_solidcraft_checks(self):
        for case in QUALIFICATION_CASES:
            slug = case["slug"]
            with self.subTest(case=slug):
                proof = proof_contract(slug)
                self.assertEqual(proof["case"], slug)
                self.assertEqual(proof["geometry"], geometry_contract(slug))
                native = proof["solidcraft_only"]
                self.assertEqual(native["native_expectation"], case["native_expectation"])
                self.assertEqual(native["generated_relationship"], case["lowering"])
                self.assertEqual(native["q5_required"], bool(case.get("q5_required")))
                self.assertEqual(native["q5_reason"], case["mutation"])
                self.assertTrue(native["q5_reason"].strip())
                self.assertEqual(
                    native["mutation"],
                    case["mutation"] if case.get("q5_required") else None,
                )

    def test_every_case_explains_q5_applicability(self):
        for case in QUALIFICATION_CASES:
            with self.subTest(case=case["slug"]):
                self.assertIn("mutation", case)
                self.assertIsInstance(case["mutation"], str)
                self.assertTrue(case["mutation"].strip())

    def test_solid_plate_cannot_match_anchored_holes_volume(self):
        contract = geometry_contract("anchored-holes")
        solid_plate_volume = 100.0 * 60.0 * 10.0
        self.assertGreater(
            abs(solid_plate_volume - contract["volume_mm3"]),
            contract["volume_tolerance_mm3"],
        )

    def test_pattern_volume_tolerance_still_rejects_one_missing_slot(self):
        contract = geometry_contract("rectangular-pattern")
        one_slot_volume = (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
        self.assertGreater(one_slot_volume, contract["volume_tolerance_mm3"])

    def test_slot_family_tolerance_still_rejects_one_missing_cut(self):
        contract = geometry_contract("slot-family")
        smallest_straight_slot_volume = (
            20.0 * 8.0 + math.pi * 4.0**2
        ) * 5.0
        self.assertGreater(
            smallest_straight_slot_volume,
            contract["volume_tolerance_mm3"],
        )

    def test_internal_feature_probes_are_3d(self):
        contract = geometry_contract("anchored-holes")
        z_values = {
            round(probe["point"][2], 6)
            for probe in contract["surface_distance_probes"]
        }
        self.assertEqual(z_values, {1.0, 5.0, 9.0})


if __name__ == "__main__":
    unittest.main()
