"""Tests for immutable qualification-container metadata and CI ownership."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import container_image_status, qualification_image


class QualificationImageTests(unittest.TestCase):
    def test_metadata_uses_toolchain_hash_not_latest(self):
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertTrue(values["reference"].startswith(
            "ghcr.io/brainboxemb/lib.py.solidcraft.forge/qualification:toolchain-"
        ))
        self.assertNotIn(":latest", values["reference"])
        self.assertEqual(len(values["image_id"]), 64)

    def test_python_and_cadcraft_come_from_toolchain(self):
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertEqual(values["python"], "3.12")
        self.assertTrue(
            values["python_image"].startswith(
                "python:3.12-slim-bookworm@sha256:"
            )
        )
        self.assertEqual(values["cadcraft"], "0.20.1")
        self.assertEqual(len(values["cadcraft_sha256"]), 64)

    def test_solidcraft_version_comes_from_version_module(self):
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertEqual(values["solidcraft"], "0.42.0")

    def test_forge_workflow_delegates_pipeline_logic(self):
        workflow = (
            qualification_image.ROOT
            / ".github"
            / "workflows"
            / "scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python scripts/forge_pipeline.py run", workflow)
        self.assertIn("docker/build-push-action@v6", workflow)

        # These are repository/pipeline concerns, not Actions concerns.
        self.assertNotIn("qualification/case_runner.py simple-box", workflow)
        self.assertNotIn("scripts/verification_gate.py", workflow)
        self.assertNotIn("scripts/generated_output.py promote-overlay", workflow)
        self.assertNotIn("site/build.py", workflow)
        self.assertNotIn("site/test_site.py", workflow)

    def test_pipeline_owns_image_smoke_and_exact_stage_rerun(self):
        pipeline = (
            qualification_image.ROOT
            / "scripts"
            / "forge_pipeline.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"qualification/case_runner.py"', pipeline)
        self.assertIn('"simple-box"', pipeline)
        self.assertIn('"--stage"', pipeline)
        self.assertIn('"mutate"', pipeline)
        self.assertIn("replay_before", pipeline)
        self.assertIn("mutate_before", pipeline)

    def test_dockerfile_contains_no_tool_version_literals(self):
        dockerfile = qualification_image.DOCKERFILE.read_text(encoding="utf-8")
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertNotIn(values["solidcraft"], dockerfile)
        self.assertNotIn(values["cadcraft"], dockerfile)
        self.assertNotIn(values["cadcraft_sha256"], dockerfile)
        self.assertNotIn(values["python_image"], dockerfile)
        self.assertIn("ARG PYTHON_IMAGE", dockerfile)
        self.assertIn("ARG SOLIDCRAFT_VERSION", dockerfile)
        self.assertIn("ARG CADCRAFT_VERSION", dockerfile)

    def test_container_manifest_present_is_not_downloaded(self):
        completed = __import__("subprocess").CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout='{"schemaVersion": 2}',
            stderr="",
        )
        with patch.object(
            container_image_status.subprocess,
            "run",
            return_value=completed,
        ) as run:
            self.assertTrue(
                container_image_status.inspect(
                    "ghcr.io/brainboxemb/example:immutable"
                )
            )

        command = run.call_args.args[0]
        self.assertEqual(command[:3], ["docker", "manifest", "inspect"])
        self.assertNotIn("pull", command)

    def test_container_manifest_unknown_is_explicitly_absent(self):
        completed = __import__("subprocess").CompletedProcess(
            args=["docker"],
            returncode=1,
            stdout="",
            stderr="manifest unknown: manifest unknown",
        )
        with patch.object(
            container_image_status.subprocess,
            "run",
            return_value=completed,
        ):
            self.assertFalse(
                container_image_status.inspect(
                    "ghcr.io/brainboxemb/example:missing"
                )
            )

    def test_container_auth_or_network_error_is_not_absent(self):
        for message in (
            "unauthorized: authentication required",
            "dial tcp: network is unreachable",
            "context deadline exceeded",
        ):
            with self.subTest(message=message):
                completed = __import__("subprocess").CompletedProcess(
                    args=["docker"],
                    returncode=1,
                    stdout="",
                    stderr=message,
                )
                with patch.object(
                    container_image_status.subprocess,
                    "run",
                    return_value=completed,
                ):
                    with self.assertRaises(
                        container_image_status.ImageLookupError
                    ):
                        container_image_status.inspect(
                            "ghcr.io/brainboxemb/example:immutable"
                        )

    def test_workflow_inspects_manifest_before_full_pull(self):
        workflow = (
            qualification_image.ROOT
            / ".github"
            / "workflows"
            / "scpf.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/container_image_status.py", workflow)
        self.assertNotIn("timeout 30s docker pull", workflow)
        self.assertIn("docker pull", workflow)

    def test_image_id_changes_when_dockerfile_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dockerfile = root / "Dockerfile"
            toolchain = root / "toolchain.json"
            dockerfile.write_text("FROM python:3.12\n", encoding="utf-8")
            toolchain.write_text(
                '{"schema": 2, "python_image": "python:3.12@sha256:x", '
                '"cadcraft": {"version": "1", "sha256": "x"}, '
                '"references": {}}\n',
                encoding="utf-8",
            )
            version_file = root / "version.py"
            version_file.write_text(
                'TESTED_SOLIDCRAFT_VERSION = "0.42.0"\n',
                encoding="utf-8",
            )

            with patch.object(qualification_image, "ROOT", root), \
                 patch.object(qualification_image, "DOCKERFILE", dockerfile), \
                 patch.object(qualification_image, "TOOLCHAIN", toolchain), \
                 patch.object(qualification_image, "VERSION_FILE", version_file):
                first = qualification_image.image_id()
                dockerfile.write_text(
                    "FROM python:3.12\nRUN true\n",
                    encoding="utf-8",
                )
                second = qualification_image.image_id()

            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
