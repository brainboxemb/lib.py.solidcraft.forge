"""Tests for immutable qualification-container metadata."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import qualification_image


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

    def test_image_workflow_only_tracks_toolchain_inputs(self):
        workflow = (
            qualification_image.ROOT
            / ".github"
            / "workflows"
            / "qualification-image.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('"docker/qualification/**"', workflow)
        self.assertIn('"qualification/toolchain.json"', workflow)
        self.assertIn('"scpf/scpf/version.py"', workflow)
        self.assertNotIn('"scpf/**"', workflow)
        self.assertNotIn('"examples/simple-box/**"', workflow)
        self.assertNotIn('"qualification/run_affected.py"', workflow)

    def test_immutable_image_is_publishable_before_main(self):
        workflow = (
            qualification_image.ROOT
            / ".github"
            / "workflows"
            / "qualification-image.yml"
        ).read_text(encoding="utf-8")
        immutable = workflow.split(
            "- name: Publish immutable qualification image", 1
        )[1].split("- name: Publish readable main alias", 1)[0]
        self.assertNotIn("github.ref == 'refs/heads/main'", immutable)

    def test_forge_workflow_consumes_image_without_building_it(self):
        workflow = (
            qualification_image.ROOT
            / ".github"
            / "workflows"
            / "forge.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("docker pull", workflow)
        self.assertIn("scripts/ci/forge_gate.py", workflow)
        self.assertNotIn("docker/build-push-action", workflow)
        self.assertNotIn("apt-get", workflow)

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
