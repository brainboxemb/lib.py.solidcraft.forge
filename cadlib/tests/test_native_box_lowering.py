"""Package-owned contract for direct parameterized Box lowering."""
from pathlib import Path
import tempfile
import unittest

from scpf.runner import run_script


MODEL = """class SimpleBox:
    length = 40.0
    width = 30.0
    height = 10.0

    def build(self):
        return Box(self.length, self.width, self.height, anchor=Anchor.BOTTOM)


SimpleBox()
"""


class NativeBoxLoweringTests(unittest.TestCase):
    def test_parameterized_box_lowers_directly_to_native_solid_box(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "model.py"
            source.write_text(MODEL, encoding="utf-8")
            commands = run_script(source)["commands"]

        feature_commands = [
            row for row in commands if row["command"] != "parameters.add"
        ]
        self.assertEqual([row["command"] for row in feature_commands], ["solid.box"])
        box = feature_commands[0]["params"]
        self.assertEqual(box["length"], "length")
        self.assertEqual(box["width"], "width")
        self.assertEqual(box["height"], "height")
        self.assertEqual(box["corner"], ["-length / 2", "-width / 2", 0])
        self.assertFalse(any(row["command"].startswith("sketch.") for row in commands))
        self.assertFalse(any(row["command"] == "solid.extrude" for row in commands))


if __name__ == "__main__":
    unittest.main()
