"""Requirement tests for exact-value and predicate verification helpers."""

from __future__ import annotations

import inspect
import json
import unittest

import cad_verification.assertions as assertions_module
from cad_verification import (
    VerificationConfigError,
    VerificationFailure,
    require_condition,
    require_equal,
)


class AssertionTests(unittest.TestCase):
    def test_r1_exact_equality_passes_with_stable_evidence(self):
        expected = {
            "type": "BoxFeature",
            "values": [1, 2, {"warning": None}],
        }
        evidence = require_equal(
            expected,
            {
                "type": "BoxFeature",
                "values": [1, 2, {"warning": None}],
            },
            label="timeline",
        )

        self.assertEqual(
            evidence,
            {
                "label": "timeline",
                "expected": expected,
                "actual": expected,
                "pass": True,
            },
        )
        self.assertEqual(
            json.dumps(evidence, sort_keys=True),
            json.dumps(
                require_equal(expected, expected, label="timeline"),
                sort_keys=True,
            ),
        )

    def test_r2_exact_equality_does_not_apply_numeric_tolerance(self):
        with self.assertRaises(VerificationFailure) as caught:
            require_equal(1.0, 1.0000001, label="exact parameter")

        self.assertEqual(
            caught.exception.evidence,
            {
                "label": "exact parameter",
                "expected": 1.0,
                "actual": 1.0000001,
                "pass": False,
            },
        )

    def test_r3_predicate_pass_and_failure_preserve_evidence(self):
        passed = require_condition(
            True,
            expected={"count": 4},
            actual={"count": 4},
            label="feature count",
        )
        self.assertEqual(passed["pass"], True)
        self.assertEqual(passed["expected"], {"count": 4})
        self.assertEqual(passed["actual"], {"count": 4})

        with self.assertRaises(VerificationFailure) as caught:
            require_condition(
                False,
                expected={"count": 4},
                actual={"count": 3},
                label="feature count",
            )
        self.assertEqual(
            caught.exception.evidence,
            {
                "label": "feature count",
                "expected": {"count": 4},
                "actual": {"count": 3},
                "pass": False,
            },
        )

    def test_r4_predicate_requires_real_boolean(self):
        for value in (0, 1, None, "", [], object()):
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(
                    VerificationConfigError,
                    "condition must be a bool",
                ):
                    require_condition(
                        value,
                        expected=True,
                        actual=value,
                    )

    def test_r5_evidence_and_label_are_validated(self):
        invalid_evidence = (
            {"bad": {1, 2}},
            float("nan"),
            object(),
        )
        for value in invalid_evidence:
            with self.subTest(value=repr(value)):
                with self.assertRaises(VerificationConfigError):
                    require_equal(value, value)
                with self.assertRaises(VerificationConfigError):
                    require_condition(
                        True,
                        expected=value,
                        actual=None,
                    )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "label must be a string or None",
        ):
            require_equal(1, 1, label=42)

    def test_r6_module_has_no_cad_or_consumer_dependencies(self):
        source = inspect.getsource(assertions_module).lower()
        forbidden = (
            "solidcraft",
            "forge",
            "trimesh",
            "cadquery",
            "build123d",
            "pythonscad",
            "pybosl2",
            "github",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)


if __name__ == "__main__":
    unittest.main()
