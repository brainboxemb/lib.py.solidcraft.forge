"""Contract tests for the generated-output publication architecture."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_site_evidence():
    path = ROOT / "site" / "evidence.py"
    spec = importlib.util.spec_from_file_location("site_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


class SiteEvidenceTests(unittest.TestCase):
    def test_each_case_resolves_its_own_native_verification_state(self):
        evidence = load_site_evidence()
        manifest = {
            "cases": {
                "verified-case": {
                    "implementations": {
                        "scpf": {
                            "status": "pass",
                            "verification_level": "q1-q6-full",
                        }
                    }
                },
                "q2-only-case": {
                    "implementations": {
                        "scpf": {
                            "status": "pass",
                            "verification_level": "affected-q1-q2",
                        }
                    }
                },
            }
        }

        first_record, first_verified = evidence.scpf_case_state(
            manifest, "verified-case"
        )
        second_record, second_verified = evidence.scpf_case_state(
            manifest, "q2-only-case"
        )
        missing_record, missing_verified = evidence.scpf_case_state(
            manifest, "missing-case"
        )

        self.assertEqual(first_record["verification_level"], "q1-q6-full")
        self.assertTrue(first_verified)
        self.assertEqual(second_record["verification_level"], "affected-q1-q2")
        self.assertFalse(second_verified)
        self.assertIsNone(missing_record)
        self.assertFalse(missing_verified)

    def test_native_verification_levels_are_explicit(self):
        evidence = load_site_evidence()
        for level in ("affected-q1-q6", "q1-q6-full", "full-q1-q6"):
            with self.subTest(level=level):
                record, verified = evidence.scpf_case_state(
                    {
                        "cases": {
                            "case": {
                                "implementations": {
                                    "scpf": {
                                        "status": "pass",
                                        "verification_level": level,
                                    }
                                }
                            }
                        }
                    },
                    "case",
                )
                self.assertIsNotNone(record)
                self.assertTrue(verified)

    def test_build_uses_per_case_state_in_both_loops(self):
        source = (ROOT / "site" / "build.py").read_text(encoding="utf-8")
        self.assertEqual(
            source.count("case_record, case_verified = scpf_case_state("),
            2,
        )


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

    def test_reused_site_evidence_tracks_build_source_commit(self):
        preview = (ROOT / ".github/workflows/preview.yml").read_text()
        site = (ROOT / ".github/workflows/site.yml").read_text()

        self.assertIn('EVIDENCE_SHA=', preview)
        self.assertIn('--evidence-sha="$EVIDENCE_SHA"', preview)
        self.assertIn('output/resolved/build.json', preview)

        self.assertIn('EVIDENCE_SHA=', site)
        self.assertIn('--evidence-sha="$EVIDENCE_SHA"', site)
        self.assertIn('generated-build/main/build.json', site)

    def test_site_only_reads_build_main_not_actions_history(self):
        workflow = (ROOT / ".github/workflows/site.yml").read_text()
        self.assertIn("ref: build", workflow)
        self.assertIn("verify-build", workflow)
        self.assertIn("--require-complete", workflow)
        self.assertNotIn("verify-current-hashes", workflow)
        self.assertIn("materialize-site-evidence", workflow)
        self.assertIn("site/provenance.py write-build", workflow)
        self.assertIn("scripts/publish_generated.py replace-stable-pages", workflow)
        self.assertNotIn("gh run", workflow)
        self.assertNotIn("actions/download-artifact", workflow)
        self.assertNotIn("reusable_qualification.py select", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)

    def test_full_workflow_uses_immutable_image_and_release_branch_gate(self):
        workflow = (ROOT / ".github/workflows/scpf.yml").read_text()
        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn('"qualification/**"', workflow)
        self.assertIn("docker pull", workflow)
        self.assertIn("steps.image.outputs.reference", workflow)
        self.assertIn("--gate full-q1-q6", workflow)
        self.assertIn("--require-complete", workflow)
        self.assertIn("scripts/publish_generated.py replace-dir", workflow)
        self.assertIn("scripts/publish_generated.py replace-stable-pages", workflow)
        self.assertNotIn("setup_solidcraft.py", workflow)
        self.assertNotIn("setup_references.py", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)

    def test_qualify_main_is_one_operational_entry(self):
        workflow = (ROOT / ".github/workflows/qualify-main.yml").read_text()
        trigger = (ROOT / ".github/workflows/qualify-main.trigger").read_text()

        self.assertIn("name: Qualify main", workflow)
        self.assertIn("branches:", workflow)
        self.assertIn("- main", workflow)
        self.assertIn('".github/workflows/qualify-main.trigger"', workflow)
        self.assertIn("workflow_dispatch: {}", workflow)
        self.assertIn("if: github.ref == 'refs/heads/main'", workflow)
        self.assertIn("scripts/qualification_image.py", workflow)
        self.assertIn("scripts/verification_gate.py", workflow)
        self.assertIn("--gate full-q1-q6", workflow)
        self.assertIn("scripts/publish_generated.py replace-dir", workflow)
        self.assertIn("scripts/publish_generated.py replace-stable-pages", workflow)
        self.assertTrue(trigger.strip())

    def test_qualify_main_does_not_become_a_release_trigger(self):
        release = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn('"SCPF full safety qualification"', release)
        self.assertNotIn('"Qualify main"', release)

    def test_agent_documents_simple_main_recovery_path(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("main -> qualification -> build/main -> Pages", agents)
        self.assertIn("Qualify main", agents)
        self.assertIn(".github/workflows/qualify-main.trigger", agents)
        self.assertIn("Do not create a temporary", agents)

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
