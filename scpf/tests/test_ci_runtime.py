"""Keep Forge runtime consumption explicit and externally owned."""

from pathlib import Path
import re
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "scpf.yml"
MODEL_VERIFY = ROOT / "scripts" / "model_verify_declarative.py"
MODEL_BATCH = ROOT / "scripts" / "model_verification_batch.py"
REFERENCE_BATCH = ROOT / "scripts" / "reference_verification_batch.py"
PR_TOOL_COMMIT = "4c1016d594368146fb9c16602f01c158e85d9afb"
MAIN_TOOL_COMMIT = "4c1016d594368146fb9c16602f01c158e85d9afb"


def configured_variable(name: str) -> str:
    """Read one quoted or plain root CAD-CI variable without a YAML dependency."""

    text = CAD_CI.read_text(encoding="utf-8")
    match = re.search(
        rf"^  {re.escape(name)}:\s*[\"']?([^\"'\s]+)[\"']?\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError(f"missing CAD-CI variable: {name}")
    return match.group(1)


class CiRuntimeContractTests(unittest.TestCase):
    """Prove Forge consumes the released external runtime roles."""

    def test_runtime_roles_are_external_immutable_releases(self):
        """Use matching SemVer role releases from docker.cad.solidcraft."""

        solidcraft = configured_variable("FORGE_RUNTIME_IMAGE")
        reference = configured_variable("REFERENCE_RUNTIME_IMAGE")
        self.assertRegex(
            solidcraft,
            r"^ghcr\.io/brainboxemb/cad-solidcraft:v\d+\.\d+\.\d+$",
        )
        self.assertRegex(
            reference,
            r"^ghcr\.io/brainboxemb/cad-reference:v\d+\.\d+\.\d+$",
        )
        self.assertEqual(
            solidcraft.rsplit(":", 1)[1],
            reference.rsplit(":", 1)[1],
        )
        self.assertEqual(solidcraft.rsplit(":", 1)[1], "v0.3.2")

    def test_runtime_consumers_use_separate_roles(self):
        """Keep model and reference execution on their own released images."""

        model_text = MODEL_BATCH.read_text(encoding="utf-8")
        reference_text = REFERENCE_BATCH.read_text(encoding="utf-8")
        self.assertIn('os.environ.get("FORGE_RUNTIME_IMAGE"', model_text)
        self.assertNotIn("REFERENCE_RUNTIME_IMAGE", model_text)
        self.assertIn('os.environ.get("REFERENCE_RUNTIME_IMAGE"', reference_text)
        self.assertNotIn('os.environ.get("FORGE_RUNTIME_IMAGE"', reference_text)

    def test_model_launcher_exposes_cold_path_timing(self):
        """Keep #484 timing decomposition visible without changing semantics."""

        text = MODEL_VERIFY.read_text(encoding="utf-8")
        for label in (
            "compile_commands_s=",
            "image_pull_s=",
            "container_start_s=",
            "python_bootstrap_s=",
            "cad_verification_import_s=",
            "definition_load_s=",
            "native_model_s=",
            "solidcraft_verification_s=",
            "inside_runtime_total_s=",
            "container_process_total_s=",
        ):
            self.assertIn(label, text)
        self.assertIn("time.perf_counter()", text)

    def test_runtime_batches_start_one_container_per_batch(self):
        model_text = MODEL_BATCH.read_text(encoding="utf-8")
        reference_text = REFERENCE_BATCH.read_text(encoding="utf-8")

        self.assertEqual(model_text.count('"docker",\n            "run"'), 1)
        self.assertEqual(reference_text.count('"docker",\n            "run"'), 1)
        self.assertIn("for row in rows:", model_text)
        self.assertIn("processed_reference_slugs", reference_text)

    def test_solidcraft_version_matches_forge(self):
        """Keep Forge's compatibility declaration explicit."""

        self.assertEqual(
            configured_variable("SOLIDCRAFT_VERSION"),
            TESTED_SOLIDCRAFT_VERSION,
        )

    def test_forge_owns_no_runtime_packaging(self):
        """Runtime build and release files belong to docker.cad.solidcraft."""

        self.assertFalse((ROOT / "docker" / "solidcraft_runtime").exists())
        self.assertFalse(
            (ROOT / ".github" / "workflows" / "solidcraft-runtime.yml").exists()
        )
        self.assertFalse((ROOT / "scripts" / "solidcraft_runtime.py").exists())

    def test_normal_workflow_delegates_to_released_cad_ci(self):
        """Keep the Forge workflow a thin CAD-CI consumer."""

        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("types: [opened, synchronize, reopened, closed]", text)

        self.assertIn("cad_ci_pr:", text)
        self.assertIn("if: github.event_name == 'pull_request'", text)
        self.assertIn(
            "uses: brainboxemb/tool.cad.ci/.github/workflows/"
            f"reusable-pr.yml@{PR_TOOL_COMMIT}",
            text,
        )
        self.assertIn("contents: write", text)
        self.assertIn("packages: read", text)
        self.assertNotIn("cleanup_pr_build:", text)
        self.assertNotIn("publish_pr_build:", text)
        self.assertNotIn("build_artifact_name: forge-cad-ci-build", text)

        self.assertIn("cad_ci_main:", text)
        self.assertIn(
            "uses: brainboxemb/tool.cad.ci/.github/workflows/"
            f"reusable-ci.yml@{MAIN_TOOL_COMMIT}",
            text,
        )
        self.assertIn("build_artifact_name: forge-cad-ci-main-build", text)
        self.assertIn("publish_main_build:", text)
        self.assertEqual(text.count("actions/download-artifact@v4"), 1)
        self.assertIn("cad-ci build fetch", text)
        self.assertIn("cad-ci build update-main", text)
        self.assertIn("--main generated-build/main", text)
        self.assertIn("--scope main", text)
        self.assertIn("--base \"$BASE_SHA\"", text)
        self.assertIn("--head \"$SOURCE_SHA\"", text)
        self.assertIn("--source-ref \"$SOURCE_REF\"", text)
        self.assertIn("--expected-source \"$SOURCE_SHA\"", text)
        self.assertIn(f"ref: {MAIN_TOOL_COMMIT}", text)

        self.assertNotIn("cleanup_existing_stale_pr_builds:", text)
        self.assertNotIn("runtime_check:", text)
        self.assertNotIn("environment_json:", text)
        self.assertNotIn("solidcraft_runtime.py", text)



if __name__ == "__main__":
    unittest.main()
