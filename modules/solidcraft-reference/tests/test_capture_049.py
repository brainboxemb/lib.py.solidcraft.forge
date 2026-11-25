from pathlib import Path
import unittest

from cad_library_solidcraft_reference import capture_snapshot


ROOT = Path(__file__).resolve().parents[3]


class CaptureSolidCraft049Reference(unittest.TestCase):
    def test_capture_exact_immutable_runtime_reference(self):
        out = (
            ROOT
            / "build"
            / "qualification"
            / "solidcraft-reference"
            / "0.49.0"
        )
        count = capture_snapshot(
            image="ghcr.io/brainboxemb/cad-solidcraft:v0.3.6",
            version="0.49.0",
            upstream_commit="10e6242c3a94e942c8fc11e78965ef1cd21e4856",
            runtime_release="v0.3.6",
            out=out,
        )
        self.assertGreaterEqual(count, 100)
        self.assertTrue((out / "commands.json").is_file())
        self.assertTrue((out / "commands.md").is_file())
        self.assertTrue((out / "SOURCE.md").is_file())


if __name__ == "__main__":
    unittest.main()
