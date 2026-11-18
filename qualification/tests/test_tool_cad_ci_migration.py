"""Contract tests for the first Forge tool.cad.ci migration phase."""

from pathlib import Path
import re
import unittest

import yaml

from scripts import bootstrap_cad_ci


ROOT = Path(__file__).resolve().parents[2]
TOOL_COMMIT = "556e8d43dde9218b28a8d991ab9f2021232e76ab"


class ToolCadCiMigrationTests(unittest.TestCase):
    def test_external_tool_is_pinned_to_released_v022_commit(self):
        """Forge must never execute moving tool.cad.ci main in CI."""

        url, sha = bootstrap_cad_ci.dependency(ROOT)
        self.assertEqual(
            url,
            "https://github.com/brainboxemb/tool.cad.ci.git",
        )
        self.assertEqual(sha, TOOL_COMMIT)

    def test_root_config_has_library_and_integration_items_only(self):
        """Phase one must not pretend native qualification is migrated."""

        config = yaml.safe_load(
            (ROOT / "cad-ci.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            config["items"],
            ["scpf/tests", "examples/simple-box"],
        )

        library = yaml.safe_load(
            (ROOT / "scpf/tests/ci.yml").read_text(encoding="utf-8")
        )
        integration = yaml.safe_load(
            (ROOT / "examples/simple-box/ci.yml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(library["kind"], "library-test")
        self.assertEqual(integration["kind"], "integration")

    def test_workflow_only_bootstraps_the_pinned_tool(self):
        """Selection and test execution stay in tested Python, not YAML."""

        workflow = (
            ROOT / ".github/workflows/scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "python scripts/bootstrap_cad_ci.py",
            workflow,
        )
        self.assertNotIn("cad-ci run", workflow)
        self.assertNotIn("cad-ci plan", workflow)

    def test_new_docs_name_the_three_real_test_layers(self):
        """New repository guidance must not present Q1/Q2 as architecture."""

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Library unit tests",
            "Integration tests",
            "Qualification",
        ):
            self.assertIn(phrase, agents)

        evidence_doc = (
            ROOT / "qualification/case_evidence.py"
        ).read_text(encoding="utf-8")
        self.assertIn("legacy keys", evidence_doc)
        self.assertIn("library unit tests", evidence_doc)


if __name__ == "__main__":
    unittest.main()
