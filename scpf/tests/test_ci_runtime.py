"""Keep the explicit Forge CI runtime expectation aligned with its build."""

from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]
CAD_CI = ROOT / "cad-ci.yml"
RUNTIME_SCRIPT = ROOT / "scripts" / "solidcraft_runtime.py"
RUNTIME_CONFIG = ROOT / "docker" / "solidcraft_runtime" / "runtime.json"
RUNTIME_DOCKERFILE = ROOT / "docker" / "solidcraft_runtime" / "Dockerfile"
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

    def test_runtime_does_not_embed_verification_library(self):
        """Keep released verification code outside the immutable CAD image."""

        config = json.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))
        self.assertNotIn("cad_verification_version", config)
        self.assertNotIn("cad_verification_commit", config)

        dockerfile = RUNTIME_DOCKERFILE.read_text(encoding="utf-8")
        self.assertNotIn("CAD_VERIFICATION_VERSION", dockerfile)
        self.assertNotIn("CAD_VERIFICATION_COMMIT", dockerfile)
        self.assertNotIn("lib.py.cad.verfication", dockerfile)

    def test_runtime_explicitly_keeps_shared_verification_dependencies(self):
        """Preinstall stable heavy dependencies without embedding app code."""

        config = json.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["pillow_spec"], ">=11,<13")
        self.assertEqual(config["trimesh_spec"], ">=4,<5")
        self.assertEqual(config["scipy_spec"], ">=1.12,<2")

    def test_runtime_image_id_uses_only_runtime_inputs(self):
        """Application-library release files may not alter the runtime hash."""

        digest = hashlib.sha256()
        for path in (
            RUNTIME_DOCKERFILE,
            RUNTIME_CONFIG,
            ROOT / "scpf" / "scpf" / "version.py",
        ):
            digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")

        self.assertEqual(runtime_metadata()["image_id"], digest.hexdigest())

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
