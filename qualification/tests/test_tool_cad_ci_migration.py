"""Contract tests for the Forge tool.cad.ci migration."""

from pathlib import Path
import unittest

import yaml

from scripts import bootstrap_cad_ci
from qualification.cases import supported_case_slugs


ROOT = Path(__file__).resolve().parents[2]
TOOL_COMMIT = "f43e13d7e1547e4caef9827848bace4744d30e17"


class ToolCadCiMigrationTests(unittest.TestCase):
    def test_external_tool_is_pinned_to_released_v040_commit(self):
        """Forge must never execute moving tool.cad.ci main in CI."""

        url, sha = bootstrap_cad_ci.dependency(ROOT)
        self.assertEqual(
            url,
            "https://github.com/brainboxemb/tool.cad.ci.git",
        )
        self.assertEqual(sha, TOOL_COMMIT)

    def test_root_config_discovers_forge_tool_and_existing_case_folders(self):
        """Step 1 migrates only the Forge tool item; examples stay unchanged."""

        config = yaml.safe_load(
            (ROOT / "cad-ci.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            config["items"],
            [
                "scpf",
                "examples/*",
                "qualification/reference_suite",
                "qualification/diagrams",
            ],
        )

        tool = yaml.safe_load(
            (ROOT / "scpf/ci.yml").read_text(encoding="utf-8")
        )
        case = yaml.safe_load(
            (ROOT / "examples/simple-box/ci.yml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(tool["id"], "forge-tool")
        self.assertEqual(tool["kind"], "tool")
        self.assertEqual(
            [step["id"] for step in tool["steps"]],
            ["tool_build", "tool_test"],
        )
        self.assertEqual(tool["steps"][0]["outputs"], ["dist"])
        self.assertEqual(case["kind"], "example")
        self.assertEqual(
            [step["id"] for step in case["steps"]],
            ["integration", "native"],
        )
        self.assertEqual(
            case["steps"][0]["outputs"],
            [
                "case/simple-box.json",
                "case/stages/simple-box/01-compile.json",
            ],
        )
        self.assertEqual(
            case["steps"][1]["outputs"],
            [
                "case/native/simple-box",
                "case/stages/simple-box/11-gate.json",
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
                    f"case/stages/{slug}/11-gate.json",
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
        self.assertIn('"--stage"', script)
        self.assertIn('"compile"', script)
        self.assertIn('"--from"', script)
        self.assertIn('"replay"', script)
        self.assertIn("FORGE_QUALIFICATION_IMAGE", script)
        self.assertIn('"docker"', script)
        self.assertIn('"--user"', script)
        self.assertIn("os.getuid()", script)
        self.assertIn("os.getgid()", script)
        self.assertIn("finalize_item_result.py", script)
        self.assertFalse((ROOT / "examples/simple-box/ci.py").exists())

    def test_generated_evidence_items_are_independent_from_examples(self):
        """Reference and diagram outputs have non-overlapping generic owners."""

        references = yaml.safe_load(
            (ROOT / "qualification/reference_suite/ci.yml").read_text(
                encoding="utf-8"
            )
        )
        diagrams = yaml.safe_load(
            (ROOT / "qualification/diagrams/ci.yml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(references["id"], "reference-suite")
        self.assertEqual(references["steps"][0]["outputs"], ["references"])
        self.assertEqual(diagrams["id"], "qualification-diagrams")
        self.assertEqual(diagrams["steps"][0]["outputs"], ["rendered"])
        self.assertNotIn("scpf/scpf/**", references["watch"])

    def test_workflow_only_bootstraps_the_pinned_tool(self):
        """Selection and test execution stay in tested Python, not YAML."""

        workflow = (
            ROOT / ".github/workflows/scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "python scripts/bootstrap_cad_ci.py",
            workflow,
        )
        self.assertIn(
            "python -m pip install -e ext/cad-ci",
            workflow,
        )
        self.assertNotIn("cad-ci run", workflow)
        self.assertNotIn("cad-ci plan", workflow)

    def test_new_docs_name_the_three_real_test_layers(self):
        """Repository guidance names the three real test layers."""

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Library unit tests",
            "Integration tests",
            "Qualification",
        ):
            self.assertIn(phrase, agents)

        qualification = (
            ROOT / "qualification/README.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "integration",
            "native_model",
            "geometry",
            "saved_design",
            "visual",
        ):
            self.assertIn(phrase, qualification)
        for legacy in (
            "case_evidence.py",
            "run_case_evidence.py",
            "run_affected.py",
        ):
            self.assertFalse((ROOT / "qualification" / legacy).exists())


if __name__ == "__main__":
    unittest.main()
