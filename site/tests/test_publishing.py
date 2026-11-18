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
            forge_version="0.11.0",
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

    def test_actions_expose_one_normal_forge_workflow_plus_image_worker(self):
        workflows = {
            path.name
            for path in (ROOT / ".github/workflows").glob("*.yml")
        }
        self.assertEqual(
            workflows,
            {"forge.yml", "qualification-image.yml"},
        )

        forge = (ROOT / ".github/workflows/forge.yml").read_text(
            encoding="utf-8"
        )
        image = (ROOT / ".github/workflows/qualification-image.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: Forge", forge)
        self.assertIn("scripts/ci/forge_plan.py", forge)
        self.assertIn("scripts/ci/forge_gate.py", forge)
        self.assertIn("scripts/ci/forge_site.py", forge)
        self.assertIn("scripts/publish_generated.py", forge)
        self.assertIn("scripts/reconcile_generated.py", forge)
        self.assertIn("workflow_dispatch:", forge)
        self.assertIn("schedule:", forge)
        self.assertIn("qualification image", image.lower())

    def test_forge_workflow_uses_immutable_image_for_native_work(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/qualification_image.py", workflow)
        self.assertIn("docker pull", workflow)
        self.assertIn("steps.image.outputs.reference", workflow)
        self.assertNotIn("setup_solidcraft.py", workflow)
        self.assertNotIn("setup_references.py", workflow)

    def test_main_recovery_is_one_forge_trigger(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text(
            encoding="utf-8"
        )
        trigger = (ROOT / "scripts/ci/forge.trigger").read_text(
            encoding="utf-8"
        )
        self.assertIn("push:", workflow)
        self.assertIn("branches: [main]", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertTrue(trigger.strip())

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("main -> qualification -> build/main -> Pages", agents)
        self.assertIn("scripts/ci/forge.trigger", agents)
        self.assertIn("one normal user-facing workflow", agents)

    def test_release_is_inside_forge_not_a_second_workflow(self):
        workflow = (ROOT / ".github/workflows/forge.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/ci/forge_release.py", workflow)
        self.assertIn("Create requested SCPF release", workflow)
        self.assertFalse(
            (ROOT / ".github/workflows/release.yml").exists()
        )

    def test_no_workflow_directly_force_pushes_generated_branches(self):
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("peaceiris/actions-gh-pages", text, path.name)
            self.assertNotIn("git push --force", text, path.name)
            self.assertNotIn("git push -f", text, path.name)

    def test_site_evidence_reuse_uses_same_risk_scope(self):
        selector = load_reuse_selector()
        self.assertTrue(
            selector.reusable_paths(
                ("site/style.css", "docs/11-generated-output.md")
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
