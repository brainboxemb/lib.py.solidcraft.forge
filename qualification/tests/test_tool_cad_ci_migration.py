"""Contract tests for the Forge tool.cad.ci migration."""

from pathlib import Path
import unittest

import yaml

from scripts import bootstrap_cad_ci
from qualification.cases import supported_case_slugs


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

    def test_root_config_discovers_owned_test_and_case_folders(self):
        """Forge keeps integration and native case ownership beside examples."""

        config = yaml.safe_load(
            (ROOT / "cad-ci.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            config["items"],
            ["scpf/tests", "examples/*"],
        )

        library = yaml.safe_load(
            (ROOT / "scpf/tests/ci.yml").read_text(encoding="utf-8")
        )
        case = yaml.safe_load(
            (ROOT / "examples/simple-box/ci.yml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(library["kind"], "library-test")
        self.assertEqual(case["kind"], "example")
        self.assertEqual(
            [step["id"] for step in case["steps"]],
            ["integration", "native"],
        )
        self.assertEqual(
            case["steps"][0]["outputs"],
            [
                "case/stages/simple-box/01-q1.json",
                "case/stages/simple-box/02-q2.json",
                "case/qualification/case-evidence/q1/simple-box.txt",
                "case/qualification/case-evidence/q2/simple-box.txt",
            ],
        )
        self.assertEqual(
            case["steps"][1]["outputs"],
            [
                "case/native/simple-box",
                "case/stages/simple-box/13-gate.json",
            ],
        )

    def test_every_supported_case_has_one_example_item(self):
        """Every native case has one non-overlapping example-owned CI item."""

        for slug in supported_case_slugs():
            with self.subTest(slug=slug):
                config_path = ROOT / "examples" / slug / "ci.yml"
                self.assertTrue(config_path.is_file(), config_path)
                config = yaml.safe_load(
                    config_path.read_text(encoding="utf-8")
                )
                self.assertEqual(config["id"], slug)
                self.assertEqual(config["kind"], "example")
                self.assertEqual(
                    [step["id"] for step in config["steps"]],
                    ["integration", "native"],
                )
                self.assertEqual(
                    config["steps"][0]["run"],
                    [
                        "python",
                        "../../scripts/example_ci.py",
                        "integration",
                    ],
                )
                self.assertEqual(
                    config["steps"][1]["run"],
                    [
                        "python",
                        "../../scripts/example_ci.py",
                        "native",
                    ],
                )
                self.assertIn(
                    f"case/stages/{slug}/13-gate.json",
                    config["steps"][1]["outputs"],
                )

    def test_shared_example_runner_uses_tool_identity_and_output_path(self):
        """SolidCraft runtime semantics remain in Forge's shared runner."""

        script = (
            ROOT / "scripts/example_ci.py"
        ).read_text(encoding="utf-8")
        self.assertIn("CAD_CI_ITEM", script)
        self.assertIn("CAD_CI_OUTPUT", script)
        self.assertIn("qualification/case_runner.py", script)
        self.assertIn('"--until"', script)
        self.assertIn('"q2"', script)
        self.assertIn('"--from"', script)
        self.assertIn('"compile"', script)
        self.assertIn("FORGE_QUALIFICATION_IMAGE", script)
        self.assertIn('"docker"', script)
        self.assertFalse((ROOT / "examples/simple-box/ci.py").exists())

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
        """Repository guidance must not present Q1/Q2 as architecture."""

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
