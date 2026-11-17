"""Command contract for the minimal attached THROUGH_ALL reproduction."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class AttachedThroughAllCommandTests(unittest.TestCase):
    def test_top_face_through_all_cut_emits_negative_direction(self):
        commands = run_script(
            ROOT / "examples/attached-through-all/scpf/model.py"
        )["commands"]

        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )
        self.assertTrue(extrude["through_all"])
        self.assertEqual(extrude["direction"], "negative")
        self.assertEqual(extrude["operation"], "cut")
        self.assertNotIn("distance", extrude)


if __name__ == "__main__":
    unittest.main()
