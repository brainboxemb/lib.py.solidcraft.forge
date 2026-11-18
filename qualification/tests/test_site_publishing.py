"""Publishing contract tests for generated Forge output."""

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

    def test_full_workflow_publishes_build_and_pages_after_gate(self):
        workflow = (
            ROOT / ".github" / "workflows" / "scpf.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('      - "site/**"', workflow)
        self.assertIn("publish_branch: build", workflow)
        self.assertIn("destination_dir: main", workflow)
        self.assertIn("publish_branch: gh-pages", workflow)
        self.assertNotIn("publish_branch: qualified-output", workflow)
        self.assertNotIn("publish_branch: preview-output", workflow)
        self.assertNotIn("ref: qualified-output", workflow)
        self.assertNotIn("ref: preview-output", workflow)
        self.assertIn("group: scpf-build-publish", workflow)
        self.assertIn("group: scpf-pages-publish", workflow)
        self.assertIn("name: scpf-build-${{ github.sha }}", workflow)
        self.assertIn("name: scpf-publish-site-${{ github.sha }}", workflow)

        gate = workflow.index("- name: Enforce qualification status")
        assemble = workflow.index("- name: Assemble main technical build")
        publish_build = workflow.index("- name: Publish main technical build")
        publish_site = workflow.index("- name: Publish stable Pages root")
        self.assertLess(gate, assemble)
        self.assertLess(assemble, publish_build)
        self.assertLess(assemble, publish_site)

    def test_pr_owns_one_build_scope_and_one_pages_preview(self):
        workflow = (
            ROOT / ".github" / "workflows" / "preview.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("publish_branch: build", workflow)
        self.assertIn(
            "destination_dir: pr/${{ github.event.pull_request.number }}",
            workflow,
        )
        self.assertIn("publish_branch: gh-pages", workflow)
        self.assertIn(
            "destination_dir: previews/pr-${{ github.event.pull_request.number }}",
            workflow,
        )
        self.assertNotIn("publish_branch: preview-output", workflow)
        self.assertNotIn("publish_branch: qualified-output", workflow)
        self.assertNotIn("/fast", workflow)
        self.assertIn("name: cleanup-build", workflow)
        self.assertIn("name: cleanup-preview", workflow)
        self.assertIn("--kind build", workflow)
        self.assertIn("--kind pages", workflow)

    def test_site_only_publication_preserves_pages_previews(self):
        workflow = (
            ROOT / ".github" / "workflows" / "site.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "python scripts/generated_output.py prepare-stable-pages",
            workflow,
        )
        self.assertIn("ref: gh-pages", workflow)
        self.assertIn("publish_branch: gh-pages", workflow)
        self.assertNotIn("publish_branch: qualified-output", workflow)
        self.assertNotIn("publish_branch: preview-output", workflow)

    def test_agent_file_records_build_and_pages_rules(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "`build` contains generated technical build",
            "`gh-pages` contains only the browseable website",
            "build/pr/<number>/",
            "gh-pages/previews/pr-<number>/",
            "`preview-output` and `qualified-output` are not part",
            "main -> technical build -> build/main/",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
