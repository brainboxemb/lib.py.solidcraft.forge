"""Publishing contract tests for generated Forge documentation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
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

    def test_full_workflow_promotes_only_main_after_qualification_gate(self):
        workflow = (
            ROOT / ".github" / "workflows" / "scpf.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('      - "site/**"', workflow)
        self.assertIn("publish_branch: qualified-output", workflow)
        self.assertNotIn("publish_branch: preview-output", workflow)
        self.assertIn("ref: qualified-output", workflow)
        self.assertIn("ref: gh-pages", workflow)
        self.assertIn("group: scpf-pages-publish", workflow)
        self.assertIn("name: scpf-publish-site-${{ github.sha }}", workflow)
        self.assertIn("actions/download-artifact@v4", workflow)
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main'",
            workflow,
        )
        self.assertNotIn("previews/$slug/full", workflow)
        self.assertNotIn("Publish qualification preview", workflow)

        gate = workflow.index("- name: Enforce qualification status")
        stable_stage = workflow.index("- name: Stage stable qualified output")
        stable_publish = workflow.index(
            "- name: Publish stable Pages root from qualified output"
        )
        self.assertLess(gate, stable_stage)
        self.assertLess(stable_stage, stable_publish)

    def test_pr_preview_publishes_one_pages_directory_directly(self):
        workflow = (
            ROOT / ".github" / "workflows" / "preview.yml"
        ).read_text(encoding="utf-8")

        verify = workflow.index("- name: Verify built PR preview provenance")
        publish = workflow.index("- name: Publish PR preview")

        self.assertIn(
            "types: [opened, synchronize, reopened, closed]",
            workflow,
        )
        self.assertNotIn("preview-output", workflow)
        self.assertNotIn("/fast", workflow)
        self.assertIn("publish_branch: gh-pages", workflow)
        self.assertIn(
            "destination_dir: previews/pr-${{ github.event.pull_request.number }}",
            workflow,
        )
        self.assertIn("actions/download-artifact@v4", workflow)
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha }}",
            workflow,
        )
        self.assertLess(verify, publish)

    def test_closed_pr_removes_only_its_hosted_preview(self):
        workflow = (
            ROOT / ".github" / "workflows" / "preview.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("name: cleanup-preview", workflow)
        self.assertIn("github.event.action == 'closed'", workflow)
        self.assertIn("python source/site/preview_cleanup.py", workflow)
        self.assertIn("--pages-root pages", workflow)
        self.assertIn(
            '--pull-request "${{ github.event.pull_request.number }}"',
            workflow,
        )
        self.assertIn("git push origin HEAD:gh-pages", workflow)

    def test_agent_file_records_single_pr_preview_and_stable_promotion(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "one hosted preview per pull request",
            "previews/pr-123/",
            "Remove that directory when the pull request closes",
            "qualified-output",
            "pull request -> verified artifact -> gh-pages preview",
            "main -> qualified-output -> stable gh-pages root",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
