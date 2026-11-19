"""Keep the explicit Forge CI runtime expectation aligned with its build."""

from pathlib import Path
import re
import subprocess
import sys
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
RUNTIME_SCRIPT = ROOT / "scripts" / "solidcraft_runtime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "scpf.yml"
REPOSITORY = "brainboxemb/lib.py.solidcraft.forge"
TOOL_COMMIT = "c2db9e6b6553052df12d2498e9436ba7be056fe6"


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


def runtime_metadata() -> dict[str, str]:
    """Resolve build-time runtime metadata through the build-owned helper."""

    output = subprocess.check_output(
        [
            sys.executable,
            str(RUNTIME_SCRIPT),
            "metadata",
            "--repository",
            REPOSITORY,
        ],
        cwd=ROOT,
        text=True,
    )
    return {
        key: value
        for line in output.splitlines()
        if "=" in line
        for key, value in (line.split("=", 1),)
    }


class CiRuntimeContractTests(unittest.TestCase):
    """Prove normal CI and runtime publication describe the same runtime."""

    def test_explicit_runtime_matches_current_build_definition(self):
        metadata = runtime_metadata()
        self.assertEqual(
            configured_variable("FORGE_RUNTIME_IMAGE"),
            metadata["reference"],
        )

    def test_explicit_solidcraft_version_matches_forge_and_runtime(self):
        metadata = runtime_metadata()
        expected = configured_variable("SOLIDCRAFT_VERSION")
        self.assertEqual(expected, TESTED_SOLIDCRAFT_VERSION)
        self.assertEqual(expected, metadata["solidcraft_version"])

    def test_normal_workflow_delegates_without_runtime_resolution(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "uses: brainboxemb/tool.cad.ci/.github/workflows/"
            f"reusable-ci.yml@{TOOL_COMMIT}",
            text,
        )
        self.assertNotIn("runtime_check:", text)
        self.assertNotIn("environment_json:", text)
        self.assertNotIn("solidcraft_runtime.py metadata", text)


if __name__ == "__main__":
    unittest.main()
