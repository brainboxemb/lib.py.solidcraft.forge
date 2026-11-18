"""Publishing/staging contract tests for generated Forge documentation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_provenance_module():
    path = ROOT / "site" / "provenance.py"
    spec = importlib.util.spec_from_file_location("site_provenance", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SitePublishingContractTests(unittest.TestCase):
    def test_provenance_round_trip_requires_passing_output(self):
        provenance = load_provenance_module()
        data = provenance.create_provenance(
            stage="stable",
            source_ref="main",
            source_commit="abc123",
            forge_version="0.10.0",
            solidcraft_version="0.42.0",
            workflow_run_id="42",
            qualification_level="q1-q6-full",
            qualification_status="pass",
        )
        provenance.validate_provenance(
            data,
            stage="stable",
            source_commit="abc123",
        )

        with self.assertRaises(ValueError):
            provenance.create_provenance(
                stage="stable",
                source_ref="main",
                source_commit="abc123",
                forge_version="0.10.0",
                solidcraft_version="0.42.0",
                workflow_run_id="42",
                qualification_level="q1-q6-full",
                qualification_status="fail",
            )

    def test_full_workflow_promotes_only_after_qualification_gate(self):
        workflow = (
            ROOT / ".github" / "workflows" / "scpf.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('      - "site/**"', workflow)
        self.assertIn("publish_branch: qualified-output", workflow)
        self.assertIn("publish_branch: preview-output", workflow)
        self.assertIn("ref: qualified-output", workflow)
        self.assertIn("ref: gh-pages", workflow)
        self.assertIn("group: scpf-pages-publish", workflow)
        self.assertIn("name: scpf-publish-site-${{ github.sha }}", workflow)
        self.assertIn("actions/download-artifact@v4", workflow)

        gate = workflow.index("- name: Enforce qualification status")
        stable_stage = workflow.index("- name: Stage stable qualified output")
        stable_publish = workflow.index(
            "- name: Publish stable Pages root from qualified output"
        )
        preview_stage = workflow.index(
            "- name: Stage qualified branch preview output"
        )
        self.assertLess(gate, preview_stage)
        self.assertLess(gate, stable_stage)
        self.assertLess(stable_stage, stable_publish)

        self.assertNotIn(
            '- name: Publish current library site',
            workflow,
        )

    def test_pr_preview_stages_before_pages_sync(self):
        workflow = (
            ROOT / ".github" / "workflows" / "preview.yml"
        ).read_text(encoding="utf-8")
        stage = workflow.index("- name: Stage PR preview output")
        checkout = workflow.index("- name: Checkout staged PR preview")
        verify = workflow.index("- name: Verify staged PR preview")
        publish = workflow.index(
            "- name: Publish browseable PR preview from staged output"
        )

        self.assertIn("publish_branch: preview-output", workflow)
        self.assertIn("ref: preview-output", workflow)
        self.assertIn("group: scpf-pages-publish", workflow)
        self.assertIn("actions/download-artifact@v4", workflow)
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha }}",
            workflow,
        )
        self.assertNotIn("force_orphan: true", workflow)
        self.assertLess(stage, checkout)
        self.assertLess(checkout, verify)
        self.assertLess(verify, publish)

    def test_agent_file_records_staging_and_promotion_rules(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Preview/staging output",
            "Stable output",
            "qualified-output",
            "gh-pages",
            "source branch -> branch-owned build -> preview page",
            "main -> qualified-output -> stable gh-pages root",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
