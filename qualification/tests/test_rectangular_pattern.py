"""Q1/Q2 contract for native rectangular feature patterns."""
import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/rectangular-pattern/scpf/model.py"


class RectangularPatternQualificationTests(unittest.TestCase):
    def test_emits_one_native_feature_pattern(self):
        commands = run_script(MODEL)["commands"]
        patterns = [
            command for command in commands
            if command["command"] == "solid.pattern.rectangular"
        ]
        self.assertEqual(len(patterns), 1)
        params = patterns[0]["params"]
        self.assertEqual(params["features"], ["Slot"])
        self.assertEqual(params["count1"], "columns")
        self.assertEqual(params["spacing1"], "pitch")
        self.assertEqual(params["count2"], "rows")
        self.assertEqual(params["spacing2"], "row_pitch")

    def test_count_parameters_are_dimensionless(self):
        commands = run_script(MODEL)["commands"]
        params = {
            command["params"]["name"]: command["params"]["unit"]
            for command in commands
            if command["command"] == "parameters.add"
        }
        self.assertEqual(params["columns"], "")
        self.assertEqual(params["rows"], "")
        self.assertEqual(params["pitch"], "mm")
        self.assertEqual(params["row_pitch"], "mm")

    def test_source_cut_is_not_expanded_in_python(self):
        commands = run_script(MODEL)["commands"]
        self.assertEqual(
            [c["command"] for c in commands].count("solid.extrude"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
