"""Contract tests for the Forge tool.cad.ci integration."""

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

    def test_root_config_discovers_tool_examples_and_qualification(self):
        """Each Forge responsibility has one consumer-owned generic CI item."""

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
                "qualification/tool_qualification",
            ],
        )

    def test_forge_tool_item_has_build_then_unit_test(self):
        """The Python tool itself has explicit build and unit-test stages."""

        tool = yaml.safe_load(
            (ROOT / "scpf/ci.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(tool["id"], "forge-tool")
        self.assertEqual(
            [step["id"] for step in tool["steps"]],
            ["tool_build", "tool_test"],
        )
        self.assertEqual(tool["steps"][0]["outputs"], ["dist"])
        self.assertFalse((ROOT / "scpf/tests/ci.yml").exists())

    def test_every_supported_example_has_tool_and_model_verification(self):
        """One example item owns command verification and SolidCraft verification."""

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
                    ["tool_verify", "model_verify"],
                )
                self.assertEqual(
                    config["steps"][0]["run"],
                    [
                        "python",
                        "../../scripts/example_ci.py",
                        "tool_verify",
                    ],
                )
                self.assertEqual(
                    config["steps"][1]["run"],
                    [
                        "python",
                        "../../scripts/example_ci.py",
                        "model_verify",
                    ],
                )
                self.assertIn(
                    f"case/model_verify/{slug}",
                    config["steps"][1]["outputs"],
                )
                self.assertIn(
                    f"case/stages/{slug}/11-result.json",
                    config["steps"][1]["outputs"],
                )

    def test_tool_qualification_depends_on_tool_and_all_models(self):
        """Qualification aggregates passing dependencies instead of rerunning CAD."""

        config = yaml.safe_load(
            (
                ROOT / "qualification/tool_qualification/ci.yml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(config["id"], "tool-qualification")
        self.assertEqual(
            [step["id"] for step in config["steps"]],
            ["tool_qualification"],
        )
        self.assertIn("forge-tool", config["needs"])
        self.assertEqual(
            set(config["needs"]) - {"forge-tool"},
            set(supported_case_slugs()),
        )

        script = (
            ROOT / "scripts/tool_qualification.py"
        ).read_text(encoding="utf-8")
        self.assertIn("model_verify", script)
        self.assertNotIn("solidcraft-cli", script)

    def test_example_runner_uses_tool_identity_and_runner_user(self):
        """SolidCraft model verification stays Forge-owned and writable."""

        script = (
            ROOT / "scripts/example_ci.py"
        ).read_text(encoding="utf-8")
        self.assertIn("CAD_CI_ITEM", script)
        self.assertIn("CAD_CI_OUTPUT", script)
        self.assertIn("qualification/case_runner.py", script)
        self.assertIn('"tool_verify"', script)
        self.assertIn('"model_verify"', script)
        self.assertIn("FORGE_QUALIFICATION_IMAGE", script)
        self.assertIn('"--user"', script)
        self.assertIn("os.getuid()", script)
        self.assertIn("os.getgid()", script)
        self.assertIn("finalize_item_result.py", script)

    def test_workflow_only_bootstraps_the_generic_tool(self):
        """Selection and execution policy stay in tested Python, not YAML."""

        workflow = (
            ROOT / ".github/workflows/scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python scripts/bootstrap_cad_ci.py", workflow)
        self.assertNotIn("cad-ci run", workflow)
        self.assertNotIn("cad-ci plan", workflow)
        self.assertIn("needs.plan.outputs.stage", workflow)
        self.assertNotIn("needs.plan.outputs.gate", workflow)

    def test_docs_use_the_five_explicit_forge_stages(self):
        """Repository guidance exposes one understandable verification model."""

        text = (
            (ROOT / "AGENTS.md").read_text(encoding="utf-8")
            + "\n"
            + (ROOT / "qualification/README.md").read_text(encoding="utf-8")
        )
        for phrase in (
            "tool_build",
            "tool_test",
            "tool_verify",
            "model_verify",
            "tool_qualification",
        ):
            self.assertIn(phrase, text)
        for legacy in (
            "affected-integration",
            "affected-native",
            "full-native",
        ):
            self.assertNotIn(legacy, text)


if __name__ == "__main__":
    unittest.main()
