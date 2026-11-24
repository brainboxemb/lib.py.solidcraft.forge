"""Requirement tests for numeric and measured-body comparison."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest

import cad_verification.comparison as comparison_module
from cad_verification import (
    BodyEnvelope,
    CheckOutcome,
    VerificationCheck,
    VerificationConfigError,
    VerificationContext,
    VerificationFailure,
    compare_bounds,
    compare_scalar,
    compare_vector,
    match_body_envelopes,
    verify,
)


class ComparisonTests(unittest.TestCase):
    def test_r1_scalar_exact_inside_on_and_outside_tolerance(self):
        self.assertTrue(compare_scalar(10, 10, 0)["pass"])
        self.assertTrue(compare_scalar(10, 10.4, 0.5)["pass"])
        self.assertTrue(compare_scalar(10, 10.5, 0.5)["pass"])

        with self.assertRaises(VerificationFailure) as caught:
            compare_scalar(10, 10.5001, 0.5, label="width")
        evidence = caught.exception.evidence
        self.assertEqual(evidence["label"], "width")
        self.assertFalse(evidence["pass"])
        self.assertGreater(evidence["delta"], evidence["tolerance"])

    def test_r1_scalar_rejects_invalid_values(self):
        invalid = (None, "1", True, float("nan"), float("inf"))
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(VerificationConfigError):
                    compare_scalar(value, 1, 0.1)
                with self.assertRaises(VerificationConfigError):
                    compare_scalar(1, value, 0.1)
        with self.assertRaises(VerificationConfigError):
            compare_scalar(1, 1, -0.1)

    def test_r2_vector_comparison(self):
        exact = compare_vector((1, 2, 3), (1, 2, 3), 0)
        self.assertEqual(exact["deltas"], [0.0, 0.0, 0.0])
        self.assertEqual(exact["max_delta"], 0.0)

        inside = compare_vector((1, 2, 3), (1.05, 1.95, 3.02), 0.1)
        self.assertTrue(inside["pass"])

        with self.assertRaises(VerificationFailure) as caught:
            compare_vector((1, 2, 3), (1, 2.2, 3), 0.1)
        self.assertAlmostEqual(caught.exception.evidence["max_delta"], 0.2)

        with self.assertRaises(VerificationConfigError):
            compare_vector((1, 2), (1, 2, 3), 0.1)
        with self.assertRaises(VerificationConfigError):
            compare_vector((), (), 0.1)

        first = compare_vector((1, 2, 3), (1, 2, 3), 0.1)
        second = compare_vector((1, 2, 3), (1, 2, 3), 0.1)
        self.assertEqual(json.dumps(first), json.dumps(second))

    def test_r3_bounds_comparison(self):
        exact = compare_bounds(
            (0, 0, 0),
            (10, 20, 30),
            (0, 0, 0),
            (10, 20, 30),
            0,
        )
        self.assertTrue(exact["pass"])

        inside = compare_bounds(
            (0, 0, 0),
            (10, 20, 30),
            (0.05, 0, 0),
            (10, 20.05, 30),
            0.1,
        )
        self.assertTrue(inside["pass"])

        for actual_min, actual_max in (
            ((0.2, 0, 0), (10, 20, 30)),
            ((0, 0, 0), (10, 20.2, 30)),
        ):
            with self.subTest(actual_min=actual_min, actual_max=actual_max):
                with self.assertRaises(VerificationFailure):
                    compare_bounds(
                        (0, 0, 0),
                        (10, 20, 30),
                        actual_min,
                        actual_max,
                        0.1,
                    )

        with self.assertRaises(VerificationConfigError):
            compare_bounds((0, 0), (1, 1, 1), (0, 0, 0), (1, 1, 1), 0)
        with self.assertRaises(VerificationConfigError):
            compare_bounds((2, 0, 0), (1, 1, 1), (0, 0, 0), (1, 1, 1), 0)

    def test_r4_body_envelopes_match_independent_of_actual_order(self):
        expected = (
            BodyEnvelope((0, 0, 0), (1, 1, 1), "left"),
            BodyEnvelope((10, 0, 0), (12, 2, 2), "right"),
        )
        actual = (
            BodyEnvelope((10.02, 0, 0), (12.02, 2, 2), "actual-right"),
            BodyEnvelope((0.01, 0, 0), (1.01, 1, 1), "actual-left"),
        )
        evidence = match_body_envelopes(expected, actual, 0.05)
        self.assertTrue(evidence["pass"])
        self.assertEqual(len(evidence["matched_pairs"]), 2)

        reversed_evidence = match_body_envelopes(
            expected,
            tuple(reversed(actual)),
            0.05,
        )
        self.assertEqual(evidence, reversed_evidence)

    def test_r4_duplicate_size_bodies_at_different_positions(self):
        expected = (
            BodyEnvelope((0, 0, 0), (1, 1, 1)),
            BodyEnvelope((5, 0, 0), (6, 1, 1)),
        )
        actual = (
            BodyEnvelope((5.01, 0, 0), (6.01, 1, 1)),
            BodyEnvelope((0.01, 0, 0), (1.01, 1, 1)),
        )
        self.assertTrue(match_body_envelopes(expected, actual, 0.05)["pass"])

    def test_r4_missing_extra_count_and_mismatch_fail_with_complete_evidence(self):
        one = BodyEnvelope((0, 0, 0), (1, 1, 1), "one")
        two = BodyEnvelope((5, 0, 0), (6, 1, 1), "two")
        far = BodyEnvelope((20, 0, 0), (21, 1, 1), "far")

        cases = (
            ((one, two), (one,)),
            ((one,), (one, two)),
            ((one, two), (one, far)),
        )
        for expected, actual in cases:
            with self.subTest(expected=len(expected), actual=len(actual)):
                with self.assertRaises(VerificationFailure) as caught:
                    match_body_envelopes(expected, actual, 0.01)
                evidence = caught.exception.evidence
                self.assertFalse(evidence["pass"])
                self.assertEqual(evidence["expected_count"], len(expected))
                self.assertEqual(evidence["actual_count"], len(actual))
                self.assertTrue(
                    evidence["unmatched_expected"]
                    or evidence["unmatched_actual"]
                )

        with self.assertRaises(VerificationFailure):
            match_body_envelopes((one,), (far,), 0.01)

    def test_r5_evidence_survives_verify_and_mismatch_becomes_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def passing(_ctx):
                return CheckOutcome.passed(
                    evidence=compare_scalar(10, 10.01, 0.1)
                )

            passed = verify(
                VerificationContext(
                    verification_id="comparison-pass",
                    input_path=root / "input",
                    output_dir=root / "pass",
                ),
                (VerificationCheck("scalar", passing),),
            )
            self.assertEqual(passed["status"], "pass")
            self.assertEqual(
                passed["checks"][0]["evidence"]["kind"],
                "scalar",
            )

            def failing(_ctx):
                compare_bounds(
                    (0, 0, 0),
                    (1, 1, 1),
                    (0, 0, 0),
                    (2, 1, 1),
                    0.01,
                )

            failed = verify(
                VerificationContext(
                    verification_id="comparison-fail",
                    input_path=root / "input",
                    output_dir=root / "fail",
                ),
                (VerificationCheck("bounds", failing),),
            )
            self.assertEqual(failed["status"], "fail")
            evidence = failed["checks"][0]["evidence"]
            self.assertEqual(evidence["kind"], "bounds")
            self.assertFalse(evidence["pass"])

    def test_r6_module_has_no_cad_dependencies(self):
        source = inspect.getsource(comparison_module).lower()
        forbidden = (
            "solidcraft",
            "forge",
            "trimesh",
            "cadquery",
            "build123d",
            "pythonscad",
            "pybosl2",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)


if __name__ == "__main__":
    unittest.main()
