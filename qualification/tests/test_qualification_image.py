"""Tests for immutable qualification-container metadata."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import qualification_image


class QualificationImageTests(unittest.TestCase):
    def test_metadata_uses_immutable_toolchain_tag(self):
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertTrue(
            values["reference"].startswith(
                "ghcr.io/brainboxemb/lib.py.solidcraft.forge/"
                "qualification:toolchain-"
            )
        )
        self.assertNotIn(":latest", values["reference"])
        self.assertEqual(len(values["image_id"]), 64)

    def test_tool_versions_have_single_sources(self):
        values = qualification_image.metadata(
            "BrainboxEmb/lib.py.solidcraft.forge"
        )
        self.assertEqual(values["solidcraft"], "0.42.0")
        self.assertEqual(values["python"], "3.12")
        self.assertTrue(
            values["python_image"].startswith(
                "python:3.12-slim-bookworm@sha256:"
            )
        )
        self.assertEqual(values["cadcraft"], "0.20.1")
        self.assertEqual(len(values["cadcraft_sha256"]), 64)

        dockerfile = qualification_image.DOCKERFILE.read_text(
            encoding="utf-8"
        )
        self.assertNotIn(values["solidcraft"], dockerfile)
        self.assertNotIn(values["cadcraft"], dockerfile)
        self.assertNotIn(values["cadcraft_sha256"], dockerfile)
        self.assertNotIn(values["python_image"], dockerfile)

    def test_image_id_changes_when_version_input_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dockerfile = root / "Dockerfile"
            toolchain = root / "toolchain.json"
            version_file = root / "version.py"
            dockerfile.write_text("ARG PYTHON_IMAGE\nFROM ${PYTHON_IMAGE}\n")
            toolchain.write_text(
                '{"schema": 2, "python_image": "python:3.12@sha256:x", '
                '"cadcraft": {"version": "1", "sha256": "x"}, '
                '"references": {}}\n',
                encoding="utf-8",
            )
            version_file.write_text(
                'TESTED_SOLIDCRAFT_VERSION = "0.42.0"\n',
                encoding="utf-8",
            )

            with patch.object(qualification_image, "ROOT", root), \
                 patch.object(qualification_image, "DOCKERFILE", dockerfile), \
                 patch.object(qualification_image, "TOOLCHAIN", toolchain), \
                 patch.object(qualification_image, "VERSION_FILE", version_file):
                first = qualification_image.image_id()
                version_file.write_text(
                    'TESTED_SOLIDCRAFT_VERSION = "0.43.0"\n',
                    encoding="utf-8",
                )
                second = qualification_image.image_id()

            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
