"""Keep Forge runtime consumption explicit and externally owned."""

from pathlib import Path
import re
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "scpf.yml"
MODEL_VERIFY = ROOT / "scripts" / "model_verify_declarative.py"
REFERENCE_VERIFY = ROOT / "scripts" / "verification_evidence.py"
TOOL_COMMIT = "bbdd473638d64e01acab69722092b2a12f99b84d"


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
        self.assertEqual(solidcraft.rsplit(":", 1)[1], "v0.2.0")

    def test_runtime_consumers_use_separate_roles(self):
        """Keep model and reference execution on their own released images."""

        model_text = MODEL_VERIFY.read_text(encoding="utf-8")
        reference_text = REFERENCE_VERIFY.read_text(encoding="utf-8")
        self.assertIn('os.environ.get("FORGE_RUNTIME_IMAGE"', model_text)
        self.assertNotIn("REFERENCE_RUNTIME_IMAGE", model_text)
        self.assertIn('os.environ.get("REFERENCE_RUNTIME_IMAGE"', reference_text)
        self.assertNotIn('os.environ.get("FORGE_RUNTIME_IMAGE"', reference_text)

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
        self.assertIn(
            "uses: brainboxemb/tool.cad.ci/.github/workflows/"
            f"reusable-ci.yml@{TOOL_COMMIT}",
            text,
        )
        self.assertIn("cad_ci_pr:", text)
        self.assertIn("types: [opened, synchronize, reopened, closed]", text)
        self.assertIn("github.event.action != 'closed'", text)
        self.assertIn("cleanup_pr_build:", text)
        self.assertIn("github.event.action == 'closed'", text)
        self.assertIn("cad-ci publish build-cleanup", text)
        self.assertIn('--pull-request "$PR_NUMBER"', text)
        self.assertIn("cad_ci_main:", text)
        self.assertIn("upload_build: true", text)
        self.assertIn("build_artifact_name: forge-cad-ci-build", text)
        self.assertIn("build_artifact_name: forge-cad-ci-main-build", text)
        self.assertNotIn("full_run: true", text)
        self.assertIn("publish_pr_build:", text)
        self.assertIn("publish_main_build:", text)
        self.assertIn("contents: write", text)
        self.assertIn("actions/download-artifact@v4", text)
        self.assertIn("cad-ci build prepare-pr", text)
        self.assertNotIn("--items simple-box", text)
        self.assertIn("cad-ci build fetch", text)
        self.assertIn("cad-ci build update-main", text)
        self.assertIn("--main generated-build/main", text)
        self.assertIn("cad-ci publish build", text)
        self.assertIn("--scope pr", text)
        self.assertIn("--scope main", text)
        self.assertIn("--base \"$BASE_SHA\"", text)
        self.assertIn("--head \"$SOURCE_SHA\"", text)
        self.assertIn("--source-ref \"$SOURCE_REF\"", text)
        self.assertIn("--expected-source \"$SOURCE_SHA\"", text)
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            text,
        )
        self.assertIn(
            f"ref: {TOOL_COMMIT}",
            text,
        )
        self.assertNotIn("runtime_check:", text)
        self.assertNotIn("environment_json:", text)
        self.assertNotIn("solidcraft_runtime.py", text)


if __name__ == "__main__":
    unittest.main()
