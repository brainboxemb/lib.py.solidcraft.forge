"""Contract tests for the generated-output publication architecture."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_reuse_selector():
    path = ROOT / "scripts" / "reusable_qualification.py"
    spec = importlib.util.spec_from_file_location("reusable_qualification", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_provenance_module():
    path = ROOT / "site" / "provenance.py"
    spec = importlib.util.spec_from_file_location("site_provenance", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SitePublishingContractTests(unittest.TestCase):
    def test_provenance_requires_immutable_build_commit(self):
        provenance = load_provenance_module()
        data = provenance.create_provenance(
            stage="stable",
            source_ref="main",
            source_commit="abc123",
            forge_version="0.10.0",
            solidcraft_version="0.42.0",
            workflow_run_id="42",
            qualification_level="per-case",
            qualification_status="pass",
            build_commit="buildsha123",
        )
        provenance.validate_provenance(
            data,
            stage="stable",
            source_commit="abc123",
        )
        self.assertEqual(data["build_commit"], "buildsha123")

    def test_pr_workflow_uses_one_gate_and_retrying_publisher(self):
        workflow = (ROOT / ".github/workflows/preview.yml").read_text()
        self.assertIn("qualification/preview_scope.py", workflow)
        self.assertIn("scripts/verification_gate.py", workflow)
        self.assertIn("scripts/merge_promotion.py", workflow)
        self.assertIn("scripts/publish_generated.py replace-dir", workflow)
        self.assertIn("scripts/publish_generated.py remove-dir", workflow)
        self.assertIn("--expected-source", workflow)
        self.assertIn("--base-commit", workflow)
        self.assertIn("resolve-preview", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)
        self.assertNotIn("git push origin", workflow)

    def test_site_only_reads_build_main_not_actions_history(self):
        workflow = (ROOT / ".github/workflows/site.yml").read_text()
        self.assertIn("ref: build", workflow)
        self.assertIn("verify-current-hashes", workflow)
        self.assertIn("materialize-site-evidence", workflow)
        self.assertIn("site/provenance.py write-build", workflow)
        self.assertIn("scripts/publish_generated.py replace-stable-pages", workflow)
        self.assertNotIn("gh run", workflow)
        self.assertNotIn("actions/download-artifact", workflow)
        self.assertNotIn("reusable_qualification.py select", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)

    def test_full_workflow_is_safety_gate_not_main_push_gate(self):
        workflow = (ROOT / ".github/workflows/scpf.yml").read_text()
        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("schedule:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("--gate full-q1-q6", workflow)
        self.assertIn("--require-complete", workflow)
        self.assertIn("scripts/publish_generated.py replace-dir", workflow)
        self.assertIn("scripts/publish_generated.py replace-stable-pages", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)

    def test_reconcile_is_scheduled_and_scoped(self):
        workflow = (ROOT / ".github/workflows/reconcile.yml").read_text()
        self.assertIn("schedule:", workflow)
        self.assertIn("scripts/reconcile_generated.py", workflow)
        script = (ROOT / "scripts" / "reconcile_generated.py").read_text()
        self.assertIn('destination=f"pr/{number}"', script)
        self.assertIn('destination=f"previews/pr-{number}"', script)

    def test_no_workflow_directly_pushes_generated_branches(self):
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("peaceiris/actions-gh-pages", text, path.name)
            self.assertNotIn("git push origin HEAD:build", text, path.name)
            self.assertNotIn("git push origin HEAD:gh-pages", text, path.name)

    def test_site_evidence_reuse_uses_same_risk_scope(self):
        selector = load_reuse_selector()
        self.assertTrue(
            selector.reusable_paths(
                ("site/build.py", "docs/11-generated-output.md")
            )
        )
        self.assertFalse(
            selector.reusable_paths(("scpf/scpf/compiler.py",))
        )

    def test_agent_file_points_to_normative_design(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/11-generated-output.md", agents)
        self.assertIn("schema-v2", agents)
        self.assertIn("scripts/publish_generated.py", agents)
        self.assertIn("immutable generated-branch commit SHA", agents)


if __name__ == "__main__":
    unittest.main()
