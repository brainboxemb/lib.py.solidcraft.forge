"""Site and publishing contract tests for generated Forge output."""

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

    def test_reused_provenance_records_original_qualification_commit(self):
        provenance = load_provenance_module()
        from tempfile import TemporaryDirectory
        import json

        with TemporaryDirectory() as tmp:
            verification = Path(tmp) / "verification.json"
            verification.write_text(
                json.dumps(
                    {
                        "verified": True,
                        "source_commit": "qualified123",
                        "forge_version": "0.10.0",
                        "solidcraft_version": "0.42.0",
                    }
                ),
                encoding="utf-8",
            )
            data = provenance.create_reused_provenance(
                stage="stable",
                source_ref="main",
                source_commit="site456",
                evidence_commit="qualified123",
                verification_file=verification,
                workflow_run_id="42",
            )

        self.assertEqual(data["source_commit"], "site456")
        self.assertEqual(data["qualification"]["level"], "q1-q6-reused")
        self.assertEqual(
            data["qualification"]["source_commit"],
            "qualified123",
        )

    def test_full_workflow_publishes_build_and_pages_after_gate(self):
        workflow = (
            ROOT / ".github" / "workflows" / "scpf.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('      - "site/**"', workflow)
        self.assertNotIn(
            '      - ".github/workflows/preview.yml"',
            workflow,
        )
        self.assertNotIn(
            '      - ".github/workflows/release.yml"',
            workflow,
        )
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
        self.assertIn(
            "if: steps.preview_scope.outputs.has_cases == 'true'",
            workflow,
        )
        self.assertIn(
            "needs.preview.outputs.has_cases == 'true'",
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

    def test_site_evidence_reuse_uses_same_risk_scope_as_prs(self):
        selector = load_reuse_selector()

        self.assertTrue(
            selector.reusable_paths(
                (
                    "site/build.py",
                    "site/tests/test_publishing.py",
                    "scripts/ci_preflight.py",
                    ".github/workflows/site.yml",
                )
            )
        )
        self.assertFalse(
            selector.reusable_paths(
                (
                    "scpf/scpf/compiler.py",
                    "scpf/tests/test_assembly_placement.py",
                )
            )
        )
        self.assertFalse(
            selector.reusable_paths(
                ("qualification/reference_validation.py",)
            )
        )

    def test_site_only_publication_preserves_pages_previews(self):
        workflow = (
            ROOT / ".github" / "workflows" / "site.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "python scripts/reusable_qualification.py scope",
            workflow,
        )
        self.assertIn(
            "python scripts/reusable_qualification.py select",
            workflow,
        )
        self.assertNotIn("grep -Ev", workflow)
        self.assertIn(
            "python scripts/generated_output.py prepare-stable-pages",
            workflow,
        )
        self.assertIn(
            "python site/provenance.py write-reused",
            workflow,
        )
        self.assertIn("--verification reused/native/verification.json", workflow)
        self.assertIn("--evidence-commit", workflow)
        self.assertIn("ref: gh-pages", workflow)
        self.assertIn("publish_branch: gh-pages", workflow)
        self.assertIn("group: scpf-pages-publish", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
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
            "A presentation-only PR does not create",
            "gh-pages/qualification/",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
