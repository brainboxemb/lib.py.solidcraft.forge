"""Tests for safe deterministic verification artifact evidence."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from cad_verification import ArtifactError
from cad_verification.evidence import artifact_record


class EvidenceTests(unittest.TestCase):
    def test_file_and_directory_hashes_change_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            output.mkdir()

            file_path = output / "model.step"
            file_path.write_text("one", encoding="utf-8")
            first_file = artifact_record(file_path, output)
            file_path.write_text("two", encoding="utf-8")
            second_file = artifact_record(file_path, output)
            self.assertNotEqual(first_file["sha256"], second_file["sha256"])

            folder = output / "renders"
            folder.mkdir()
            image = folder / "front.txt"
            image.write_text("one", encoding="utf-8")
            first_dir = artifact_record(folder, output)
            image.write_text("two", encoding="utf-8")
            second_dir = artifact_record(folder, output)
            self.assertNotEqual(first_dir["sha256"], second_dir["sha256"])

    def test_missing_and_out_of_root_artifacts_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            output.mkdir()

            with self.assertRaises(ArtifactError):
                artifact_record(output / "missing.step", output)

            outside = root / "outside.step"
            outside.write_text("x", encoding="utf-8")
            with self.assertRaises(ArtifactError):
                artifact_record(outside, output)

    def test_symlink_artifact_is_rejected_when_supported_by_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            output.mkdir()
            target = output / "target.txt"
            target.write_text("x", encoding="utf-8")
            link = output / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")

            with self.assertRaises(ArtifactError):
                artifact_record(link, output)


if __name__ == "__main__":
    unittest.main()
