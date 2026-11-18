"""Tests for the single Forge workflow planner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_scope():
    path = ROOT / "scripts" / "forge_scope.py"
    spec = importlib.util.spec_from_file_location("forge_scope", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ForgeScopeTests(unittest.TestCase):
    def setUp(self):
        self.scope = load_scope()

    def test_pr_presentation_change_is_preflight_only(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("docs/changes/0041-single-forge-workflow.md",),
        )
        self.assertEqual(plan["operation"], "pr")
        self.assertEqual(plan["gate"], "preflight")
        self.assertFalse(plan["needs_image"])

    def test_pipeline_only_change_uses_one_native_smoke_not_full_catalog(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=(
                ".github/workflows/scpf.yml",
                "scripts/forge_scope.py",
                "scripts/forge_pipeline.py",
                "scripts/ci_preflight.py",
                "qualification/tests/test_forge_pipeline.py",
                "site/tests/test_qualification_image.py",
                "AGENTS.md",
            ),
        )
        self.assertEqual(plan["gate"], "preflight")
        self.assertTrue(plan["pipeline_smoke"])
        self.assertTrue(plan["needs_image"])

    def test_native_case_change_selects_affected_q1_q6(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("examples/simple-box/scpf/model.py",),
        )
        self.assertEqual(plan["gate"], "affected-q1-q6")
        self.assertEqual(plan["cases"], "simple-box")

    def test_main_never_promotes_q1_q2_only_case_evidence(self):
        pr = self.scope.make_plan(
            event_name="pull_request",
            paths=("examples/simple-box/build123d/model.py",),
        )
        main = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=("examples/simple-box/build123d/model.py",),
        )
        self.assertEqual(pr["gate"], "affected-q1-q2")
        self.assertTrue(pr["reference_smoke"])
        self.assertEqual(main["gate"], "affected-q1-q6")
        self.assertEqual(main["cases"], "simple-box")

    def test_main_presentation_change_reuses_existing_build(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=("site/style.css",),
        )
        self.assertEqual(plan["gate"], "preflight")
        self.assertTrue(plan["site_only"])

    def test_forge_trigger_forces_full_main(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=(".github/workflows/forge.trigger",),
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertTrue(plan["needs_image"])
        self.assertFalse(plan["site_only"])

    def test_manual_run_is_full_recovery_without_release(self):
        plan = self.scope.make_plan(
            event_name="workflow_dispatch",
            ref_name="main",
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertFalse(plan["release"])

    def test_main_version_change_is_release_candidate(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=("scpf/pyproject.toml", "CHANGELOG.md"),
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertTrue(plan["release"])

    def test_manual_run_off_main_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "only allowed on main"):
            self.scope.make_plan(
                event_name="workflow_dispatch",
                ref_name="feature/test",
            )

    def test_weekly_schedule_is_full(self):
        plan = self.scope.make_plan(
            event_name="schedule",
            schedule=self.scope.WEEKLY_FULL_CRON,
        )
        self.assertEqual(plan["operation"], "main")
        self.assertEqual(plan["gate"], "full-q1-q6")

    def test_daily_schedule_is_reconcile_only(self):
        plan = self.scope.make_plan(
            event_name="schedule",
            schedule=self.scope.RECONCILE_CRON,
        )
        self.assertEqual(plan["operation"], "reconcile")

    def test_closed_pr_is_cleanup_only(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            event_action="closed",
        )
        self.assertEqual(plan["operation"], "cleanup")

    def test_contract_snapshot_needs_image(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("docs/vendor/solidcraft/0.42.0/runtime/contracts/solid.box.json",),
        )
        self.assertTrue(plan["contracts"])
        self.assertTrue(plan["needs_image"])


if __name__ == "__main__":
    unittest.main()
