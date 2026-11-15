"""Qualification guard for unsupported copied Placement rotation."""

from pathlib import Path
import unittest

from scpf.compiler import ModelError
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class RotatedCopyPlacementCommandTests(unittest.TestCase):
    def test_rotated_copy_is_rejected_before_native_move_fallback(self):
        with self.assertRaisesRegex(
            ModelError,
            "requires one occurrence at identity",
        ):
            run_script(
                ROOT / "examples/rotated-copy-placement/scpf/model.py"
            )


if __name__ == "__main__":
    unittest.main()
