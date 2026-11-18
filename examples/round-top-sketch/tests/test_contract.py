"""Q2 contract for TOP-attached Sketches on round bodies."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples/round-top-sketch/scpf/model.py"


class RoundTopSketchQualificationTests(unittest.TestCase):
    def setUp(self):
        self.commands = run_script(MODEL)["commands"]

    def test_top_face_query_is_used_after_circular_base_extrusion(self):
        names = [row["command"] for row in self.commands]
        self.assertEqual(names.count("model.faces"), 1)
        self.assertEqual(names.count("sketch.create"), 2)
        self.assertEqual(names.count("solid.extrude"), 2)

        face_index = names.index("model.faces")
        second_sketch_index = [
            i for i, name in enumerate(names)
            if name == "sketch.create"
        ][1]
        self.assertLess(face_index, second_sketch_index)

        query = self.commands[face_index]
        self.assertEqual(query["params"], {"body": "RoundTopSketch"})
        for spec in query["bind"].values():
            self.assertEqual(
                spec["where"],
                {"plane_normal": [0, 0, 1]},
            )
            self.assertEqual(spec["max"], "area")

        hub = self.commands[second_sketch_index]["params"]
        self.assertEqual(hub["name"], "Hub")
        self.assertEqual(hub["plane"]["body"], "RoundTopSketch")


if __name__ == "__main__":
    unittest.main()
