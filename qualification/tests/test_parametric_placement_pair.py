"""Qualification guard for unsupported symmetric parametric Placement."""

from pathlib import Path
import unittest

from scpf.compiler import ModelError
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class ParametricPlacementPairCommandTests(unittest.TestCase):
    def test_symmetric_parametric_pair_is_rejected_before_native_lowering(self):
        with self.assertRaisesRegex(
            ModelError,
            "requires one occurrence at identity",
        ):
            run_script(
                ROOT / "examples/parametric-placement-pair/scpf/model.py"
            )


if __name__ == "__main__":
    unittest.main()
