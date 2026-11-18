"""Tests for the single Forge workflow planner."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / "scripts" / "ci"
sys.path.insert(0, str(CI))

import forge_plan  # noqa: E402


class ForgePlanTests(unittest.TestCase):
    def plan(self, paths, *, event="pull_request", ref="feature/test"):
        with patch.object(forge_plan, "changed_paths", return_value=tuple(paths)):
            return forge_plan.make_plan(
                event_name=event,
                base="base",
                head="head",
                ref_name=ref,
                pull_request=12 if event == "pull_request" else None,
            )

    def test_presentation_pr_is_preflight_only(self):
        plan = self.plan(("docs/readme.md",))
        self.assertEqual(plan["gate"], "preflight")
        self.assertFalse(plan["has_build"])
        self.assertEqual(plan["publication"], "preview")

    def test_forge_pipeline_refactor_runs_one_simple_box_native_smoke(self):
        plan = self.plan(
            (
                ".github/workflows/scpf.yml",
                ".github/workflows/forge.yml",
                "qualification/impact.py",
                "scripts/ci/forge_plan.py",
                "site/tests/test_publishing.py",
                "docs/11-generated-output.md",
                "AGENTS.md",
            )
        )
        self.assertEqual(plan["gate"], "affected-q1-q6")
        self.assertEqual(plan["cases"], ["simple-box"])
        self.assertTrue(plan["has_build"])

    def test_pipeline_change_does_not_downgrade_real_forge_change(self):
        plan = self.plan(
            (
                ".github/workflows/forge.yml",
                "scpf/scpf/compiler.py",
            )
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertEqual(plan["cases"], [])

    def test_native_sensitive_pr_stays_affected(self):
        plan = self.plan(("examples/simple-box/scpf/model.py",))
        self.assertEqual(plan["gate"], "affected-q1-q6")
        self.assertEqual(plan["cases"], ["simple-box"])

    def test_technical_main_push_is_one_full_qualification(self):
        plan = self.plan(
            ("examples/simple-box/scpf/model.py",),
            event="push",
            ref="main",
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertEqual(plan["cases"], [])
        self.assertEqual(plan["publication"], "stable")

    def test_presentation_main_reuses_build_main(self):
        plan = self.plan(("site/style.css",), event="push", ref="main")
        self.assertEqual(plan["gate"], "preflight")
        self.assertTrue(plan["site_only"])
        self.assertEqual(plan["publication"], "stable")

    def test_trigger_forces_full_main(self):
        plan = self.plan(
            ("scripts/ci/forge.trigger",),
            event="push",
            ref="main",
        )
        self.assertEqual(plan["gate"], "full-q1-q6")
        self.assertTrue(plan["full"])

    def test_manual_and_schedule_are_full_without_diff(self):
        for event in ("workflow_dispatch", "schedule"):
            with self.subTest(event=event):
                plan = forge_plan.make_plan(
                    event_name=event,
                    base="",
                    head="head",
                    ref_name="main",
                )
                self.assertEqual(plan["gate"], "full-q1-q6")
                self.assertTrue(plan["full"])
                self.assertTrue(plan["contracts"])


if __name__ == "__main__":
    unittest.main()
