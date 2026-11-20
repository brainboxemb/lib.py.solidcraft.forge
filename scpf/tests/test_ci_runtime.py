"""Keep Forge runtime consumption explicit and externally owned."""

from pathlib import Path
import re
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "scpf.yml"
TOOL_COMMIT = "c60bf64a393dff33440d22e9e9347cbbaba71c4b"


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
    """Prove Forge consumes one released external CAD runtime."""

    def test_runtime_is_external_immutable_release(self):
        """Use a SemVer release from docker.cad.solidcraft."""

        reference = configured_variable("FORGE_RUNTIME_IMAGE")
        self.assertRegex(
            reference,
            r"^ghcr\.io/brainboxemb/cad-solidcraft:v\d+\.\d+\.\d+$",
        )

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
        self.assertNotIn("runtime_check:", text)
        self.assertNotIn("environment_json:", text)
        self.assertNotIn("solidcraft_runtime.py", text)


if __name__ == "__main__":
    unittest.main()
