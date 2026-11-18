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

    def test_image_id_changes_when_dockerfile_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dockerfile = root / "Dockerfile"
            toolchain = root / "toolchain.json"
            dockerfile.write_text("FROM python:3.12\n", encoding="utf-8")
            toolchain.write_text('{"schema": 1}\n', encoding="utf-8")

            with patch.object(qualification_image, "ROOT", root), \
                 patch.object(qualification_image, "DOCKERFILE", dockerfile), \
                 patch.object(qualification_image, "TOOLCHAIN", toolchain):
                first = qualification_image.image_id()
                dockerfile.write_text(
                    "FROM python:3.12\nRUN true\n",
                    encoding="utf-8",
                )
                second = qualification_image.image_id()

            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
