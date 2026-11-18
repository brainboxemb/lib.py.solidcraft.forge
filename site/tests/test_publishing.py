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

    def test_actions_expose_exactly_one_forge_workflow(self):
        workflows = sorted(
            path.name
            for path in (ROOT / ".github" / "workflows").glob("*.yml")
        )
        self.assertEqual(workflows, ["forge.yml"])
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        self.assertIn("name: Forge", workflow)
        self.assertIn("workflow_dispatch: {}", workflow)
        self.assertIn('cron: "17 3 * * 1"', workflow)
        self.assertIn('cron: "41 4 * * *"', workflow)

    def test_forge_workflow_owns_normal_verification_and_publication(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        for required in (
            "scripts/forge_scope.py",
            "scripts/ci_preflight.py",
            "scripts/qualification_image.py",
            "scripts/verification_gate.py",
            "scripts/generated_output.py promote-overlay",
            "scripts/publish_generated.py replace-dir",
            "scripts/publish_generated.py replace-stable-pages",
            "scripts/publish_generated.py remove-dir",
            "scripts/reconcile_generated.py",
            "scripts/release/validate_release.py",
            "site/build.py",
            "site/test_site.py",
        ):
            with self.subTest(required=required):
                self.assertIn(required, workflow)

        self.assertNotIn("gh workflow run", workflow)
        self.assertNotIn("peaceiris/actions-gh-pages", workflow)
        self.assertNotIn("setup_solidcraft.py", workflow)
        self.assertNotIn("setup_references.py", workflow)

    def test_forge_workflow_reuses_immutable_image_and_has_one_case_pipeline_smoke(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        self.assertIn("docker pull", workflow)
        self.assertIn("docker/build-push-action@v6", workflow)
        self.assertIn("qualification/case_runner.py simple-box", workflow)
        self.assertIn("--stage mutate", workflow)
        self.assertIn("steps.image_cache.outputs.exists != 'true'", workflow)

    def test_reused_site_evidence_tracks_build_source_commit(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        self.assertIn("evidence_sha=", workflow)
        self.assertIn('--evidence-sha="$evidence_sha"', workflow)
        self.assertIn("output/resolved/build.json", workflow)
        self.assertIn('generated-build/main', workflow)

    def test_forge_recovery_trigger_is_repository_native_and_release_independent(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        trigger = (ROOT / ".github" / "workflows" / "forge.trigger").read_text()
        planner = (ROOT / "scripts/forge_scope.py").read_text()
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertTrue(trigger.strip())
        self.assertIn('.github/workflows/forge.trigger', planner)
        self.assertIn('release": False', planner)
        self.assertIn("main -> qualification -> build/main -> Pages", agents)
        self.assertIn("Forge", agents)
        self.assertIn(".github/workflows/forge.trigger", agents)

    def test_generated_branch_writes_use_retrying_publisher(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text()
        self.assertNotIn("git push origin HEAD:build", workflow)
        self.assertNotIn("git push origin HEAD:gh-pages", workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertGreaterEqual(
            workflow.count("scripts/publish_generated.py"),
            5,
        )

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
