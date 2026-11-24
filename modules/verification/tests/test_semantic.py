"""Requirement tests for semantic result composition."""

from __future__ import annotations

import inspect
import json
import unittest

import cad_verification.semantic as semantic_module
from cad_verification import (
    SemanticCheck,
    SemanticResultError,
    VerificationConfigError,
    compose_item_results,
    compose_semantic_result,
    require_semantic_pass,
    semantic_checks_from_report,
)


class SemanticCompositionTests(unittest.TestCase):
    def test_r1_all_statuses_and_invalid_input(self):
        statuses = (
            "pass",
            "fail",
            "error",
            "missing",
            "review",
            "blocked",
            "not-required",
            "skipped",
        )
        for status in statuses:
            with self.subTest(status=status):
                check = SemanticCheck(
                    "custom_check",
                    status,
                    required=False,
                    reason="reason",
                    evidence={"value": 1},
                )
                self.assertEqual(check.status, status)
                self.assertEqual(check.to_evidence()["name"], "custom_check")

        with self.assertRaises(VerificationConfigError):
            SemanticCheck("Bad Name", "pass")
        with self.assertRaises(VerificationConfigError):
            SemanticCheck("custom", "unknown")
        with self.assertRaises(VerificationConfigError):
            SemanticCheck("custom", "pass", required="yes")
        with self.assertRaises(VerificationConfigError):
            SemanticCheck("custom", "pass", evidence={1, 2})

    def test_r2_required_precedence_and_optional_checks(self):
        cases = (
            (("error", "fail", "missing"), "error"),
            (("fail", "missing", "review"), "fail"),
            (("missing", "review", "blocked"), "incomplete"),
            (("review", "blocked", "pass"), "review"),
            (("blocked", "pass"), "blocked"),
            (("pass", "skipped", "not-required"), "pass"),
        )
        for statuses, expected in cases:
            checks = tuple(
                SemanticCheck(f"check_{index}", status)
                for index, status in enumerate(statuses)
            )
            with self.subTest(statuses=statuses):
                self.assertEqual(
                    compose_semantic_result(checks)["status"],
                    expected,
                )

        optional_failures = compose_semantic_result(
            (
                SemanticCheck("required", "pass", required=True),
                SemanticCheck("optional_fail", "fail", required=False),
                SemanticCheck("optional_error", "error", required=False),
                SemanticCheck("optional_missing", "missing", required=False),
            )
        )
        self.assertEqual(optional_failures["status"], "pass")

        with self.assertRaises(VerificationConfigError):
            compose_semantic_result(())
        with self.assertRaises(VerificationConfigError):
            compose_semantic_result(
                (
                    SemanticCheck("same", "pass"),
                    SemanticCheck("same", "pass"),
                )
            )

    def test_r3_custom_names_without_domain_policy(self):
        result = compose_semantic_result(
            (
                SemanticCheck("alpha_check", "pass"),
                SemanticCheck("beta_check", "pass"),
            )
        )
        self.assertEqual(
            [row["name"] for row in result["checks"]],
            ["alpha_check", "beta_check"],
        )

        source = inspect.getsource(semantic_module).lower()
        forbidden = (
            "native_model",
            "saved_design",
            "required_views",
            ".cad-ci",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)

    def test_r4_evidence_order_and_json_are_preserved(self):
        checks = (
            SemanticCheck(
                "first",
                "pass",
                evidence={"path": "a.json", "values": [1, 2]},
            ),
            SemanticCheck(
                "second",
                "review",
                required=False,
                reason="manual",
                evidence={"path": "b.json"},
            ),
        )
        first = compose_semantic_result(checks)
        second = compose_semantic_result(checks)
        self.assertEqual(
            [row["name"] for row in first["checks"]],
            ["first", "second"],
        )
        self.assertEqual(
            first["checks"][0]["evidence"],
            {"path": "a.json", "values": [1, 2]},
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )

    def test_r5_require_pass_accepts_only_pass(self):
        passing = compose_semantic_result(
            (SemanticCheck("one", "pass"),)
        )
        self.assertEqual(require_semantic_pass(passing), passing)

        for status in ("fail", "error", "missing", "review", "blocked"):
            result = compose_semantic_result(
                (SemanticCheck("one", status),)
            )
            with self.subTest(status=status):
                with self.assertRaises(SemanticResultError) as caught:
                    require_semantic_pass(result)
                self.assertEqual(caught.exception.evidence, result)

    def test_r6_aggregate_composition_and_precedence(self):
        passing = compose_semantic_result(
            (SemanticCheck("check", "pass"),)
        )
        failing = compose_semantic_result(
            (SemanticCheck("check", "fail"),)
        )
        incomplete = compose_semantic_result(
            (SemanticCheck("check", "missing"),)
        )

        result = compose_item_results(
            (("one", passing), ("two", passing))
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            [row["item_id"] for row in result["items"]],
            ["one", "two"],
        )

        self.assertEqual(
            compose_item_results(
                (("one", passing), ("two", failing))
            )["status"],
            "fail",
        )
        self.assertEqual(
            compose_item_results(
                (("one", passing), ("two", incomplete))
            )["status"],
            "incomplete",
        )

        with self.assertRaises(VerificationConfigError):
            compose_item_results(())
        with self.assertRaises(VerificationConfigError):
            compose_item_results(
                (("same", passing), ("same", passing))
            )

    def test_r7_module_has_no_repository_or_publication_behavior(self):
        source = inspect.getsource(semantic_module).lower()
        forbidden = (
            "tool.cad.ci",
            "scons",
            "git push",
            "gh-pages",
            "copytree",
            "shutil",
            "subprocess",
            "materializ",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source)

    def test_r8_existing_report_adapter(self):
        report = {
            "schema": "cad-verification",
            "schema_version": 1,
            "verification_id": "sample",
            "status": "fail",
            "checks": [
                {
                    "id": "first",
                    "status": "pass",
                    "reason": None,
                    "error": None,
                    "evidence": {"value": 1},
                    "artifacts": [{"path": "first.json"}],
                },
                {
                    "id": "second",
                    "status": "skipped",
                    "reason": "not used",
                    "error": None,
                    "evidence": {"value": 2},
                    "artifacts": [],
                },
                {
                    "id": "third",
                    "status": "fail",
                    "reason": None,
                    "error": "mismatch",
                    "evidence": {"expected": 1, "actual": 2},
                    "artifacts": [{"path": "third.json"}],
                },
                {
                    "id": "fourth",
                    "status": "error",
                    "reason": None,
                    "error": "RuntimeError: failed",
                    "evidence": {},
                    "artifacts": [],
                },
            ],
        }
        checks = semantic_checks_from_report(report)
        self.assertEqual(
            [check.status for check in checks],
            ["pass", "skipped", "fail", "error"],
        )
        self.assertEqual(
            checks[0].evidence["artifacts"],
            [{"path": "first.json"}],
        )
        self.assertEqual(
            checks[2].evidence["evidence"],
            {"expected": 1, "actual": 2},
        )
        self.assertEqual(checks[1].reason, "not used")

        with self.assertRaises(VerificationConfigError):
            semantic_checks_from_report({"schema": "other", "checks": []})


if __name__ == "__main__":
    unittest.main()
