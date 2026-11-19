"""Tests for Forge planning with explicit verification stages."""

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

    def test_presentation_change_needs_no_tool_stage(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("docs/changes/0041-single-forge-workflow.md",),
        )
        self.assertEqual(plan["operation"], "pr")
        self.assertEqual(plan["stage"], "none")
        self.assertFalse(plan["needs_image"])

    def test_pipeline_change_runs_pipeline_verification(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=(
                ".github/workflows/scpf.yml",
                "scripts/forge_scope.py",
                "scripts/forge_pipeline.py",
            ),
        )
        self.assertEqual(plan["stage"], "none")
        self.assertTrue(plan["verify_pipeline"])
        self.assertTrue(plan["needs_image"])

    def test_diagram_change_selects_diagram_verification(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("qualification/diagrams/corner-bracket-goal.cadcraft.json",),
        )
        self.assertEqual(plan["stage"], "none")
        self.assertTrue(plan["verify_diagrams"])
        self.assertTrue(plan["needs_image"])

    def test_example_model_change_selects_model_verify(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("examples/simple-box/scpf/model.py",),
        )
        self.assertEqual(plan["stage"], "model_verify")
        self.assertEqual(plan["cases"], "simple-box")

    def test_reference_change_selects_tool_verify_on_pr(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("examples/simple-box/build123d/model.py",),
        )
        self.assertEqual(plan["stage"], "tool_verify")
        self.assertEqual(plan["cases"], "simple-box")
        self.assertTrue(plan["verify_references"])

    def test_main_never_replaces_model_result_with_tool_verify_only(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=("examples/simple-box/build123d/model.py",),
        )
        self.assertEqual(plan["stage"], "model_verify")
        self.assertEqual(plan["cases"], "simple-box")

    def test_trigger_selects_tool_qualification(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=(".github/workflows/forge.trigger",),
        )
        self.assertEqual(plan["stage"], "tool_qualification")
        self.assertTrue(plan["verify_references"])
        self.assertTrue(plan["verify_diagrams"])

    def test_manual_main_run_selects_tool_qualification(self):
        plan = self.scope.make_plan(
            event_name="workflow_dispatch",
            ref_name="main",
        )
        self.assertEqual(plan["stage"], "tool_qualification")
        self.assertFalse(plan["release"])

    def test_version_change_is_release_candidate_and_tool_qualification(self):
        plan = self.scope.make_plan(
            event_name="push",
            ref_name="main",
            paths=("scpf/pyproject.toml", "CHANGELOG.md"),
        )
        self.assertEqual(plan["stage"], "tool_qualification")
        self.assertTrue(plan["release"])

    def test_weekly_schedule_selects_tool_qualification(self):
        plan = self.scope.make_plan(
            event_name="schedule",
            schedule=self.scope.WEEKLY_FULL_CRON,
        )
        self.assertEqual(plan["operation"], "main")
        self.assertEqual(plan["stage"], "tool_qualification")

    def test_daily_schedule_is_reconcile_only(self):
        plan = self.scope.make_plan(
            event_name="schedule",
            schedule=self.scope.RECONCILE_CRON,
        )
        self.assertEqual(plan["operation"], "reconcile")
        self.assertEqual(plan["stage"], "none")

    def test_closed_pr_is_cleanup_only(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            event_action="closed",
        )
        self.assertEqual(plan["operation"], "cleanup")

    def test_contract_snapshot_requires_solidcraft_image(self):
        plan = self.scope.make_plan(
            event_name="pull_request",
            paths=("docs/vendor/solidcraft/0.42.0/runtime/contracts/solid.box.json",),
        )
        self.assertTrue(plan["verify_contracts"])
        self.assertTrue(plan["needs_image"])


if __name__ == "__main__":
    unittest.main()
