"""Tests for the explicit verification request contract."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from cad_verification import (
    CheckOutcome,
    VerificationCheck,
    VerificationConfigError,
    VerificationContext,
    VerificationFailure,
    verify,
)


class VerificationTests(unittest.TestCase):
    def context(self, root: Path) -> VerificationContext:
        return VerificationContext(
            verification_id="simple-box",
            input_path=root / "solidcraft.json",
            output_dir=root / "output",
            metadata={"engine": "test"},
        )

    def test_passing_checks_run_in_order_and_write_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []

            def build(ctx):
                calls.append("build")
                target = ctx.output_dir / "model.step"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("STEP\n", encoding="utf-8")
                return CheckOutcome.passed(
                    evidence={"body_count": 1},
                    artifacts=(target,),
                )

            def geometry(ctx):
                calls.append("geometry")
                return None

            report = verify(
                self.context(root),
                (
                    VerificationCheck("build", build),
                    VerificationCheck("geometry", geometry),
                ),
            )

            self.assertEqual(calls, ["build", "geometry"])
            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                [row["status"] for row in report["checks"]],
                ["pass", "pass"],
            )
            stored = json.loads(
                (root / "output/verification.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(stored, report)
            self.assertEqual(
                stored["checks"][0]["artifacts"][0]["path"],
                "model.step",
            )

    def test_skip_is_recorded_and_stays_successful(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = verify(
                self.context(root),
                (
                    VerificationCheck(
                        "mutation",
                        lambda ctx: CheckOutcome.skipped(
                            "model has no saved-design mutation"
                        ),
                    ),
                ),
            )
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["checks"][0]["status"], "skipped")

    def test_expected_failure_stops_later_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []

            def geometry(ctx):
                calls.append("geometry")
                raise VerificationFailure(
                    "body count mismatch",
                    evidence={"expected": 1, "actual": 2},
                )

            def render(ctx):
                calls.append("render")

            report = verify(
                self.context(root),
                (
                    VerificationCheck("geometry", geometry),
                    VerificationCheck("render", render),
                ),
            )
            self.assertEqual(calls, ["geometry"])
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["checks"][0]["status"], "fail")
            self.assertEqual(
                report["checks"][0]["evidence"]["actual"],
                2,
            )

    def test_unexpected_exception_is_error_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []

            def build(ctx):
                calls.append("build")
                raise RuntimeError("engine unavailable")

            def geometry(ctx):
                calls.append("geometry")

            report = verify(
                self.context(root),
                (
                    VerificationCheck("build", build),
                    VerificationCheck("geometry", geometry),
                ),
            )
            self.assertEqual(calls, ["build"])
            self.assertEqual(report["status"], "error")
            self.assertIn("RuntimeError", report["checks"][0]["error"])

    def test_duplicate_and_invalid_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = self.context(root)

            with self.assertRaises(VerificationConfigError):
                verify(context, ())

            with self.assertRaises(VerificationConfigError):
                verify(
                    context,
                    (
                        VerificationCheck("build", lambda ctx: None),
                        VerificationCheck("build", lambda ctx: None),
                    ),
                )

            with self.assertRaises(VerificationConfigError):
                verify(
                    VerificationContext(
                        verification_id="Simple Box",
                        input_path=root / "input",
                        output_dir=root / "output",
                    ),
                    (),
                )


if __name__ == "__main__":
    unittest.main()
