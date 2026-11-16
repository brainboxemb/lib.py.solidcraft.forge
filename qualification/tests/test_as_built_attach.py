"""Qualification guard for unsupported copied as-built attachment."""

from pathlib import Path
import unittest

from scpf.compiler import ModelError
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class AsBuiltAttachCommandTests(unittest.TestCase):
    def test_prepositioned_as_built_occurrence_is_rejected_replay_first(self):
        with self.assertRaisesRegex(
            ModelError,
            "rotated relationship Placement is not replay-safe",
        ):
            run_script(ROOT / "examples/as-built-attach/scpf/model.py")


if __name__ == "__main__":
    unittest.main()
