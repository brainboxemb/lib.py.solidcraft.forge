"""integration command contract for TOP-attached Sketch after native chamfer."""

import unittest
from pathlib import Path

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/top-sketch-after-chamfer/scpf/model.py"


class TopSketchAfterChamferQualificationTests(unittest.TestCase):
    def setUp(self):
        self.document = run_script(MODEL)
        self.commands = self.document["commands"]

    def test_chamfer_precedes_native_face_query_and_attached_sketch(self):
        names = [row["command"] for row in self.commands]
        self.assertEqual(names.count("solid.box"), 1)
        self.assertEqual(names.count("solid.chamfer"), 1)
        self.assertEqual(names.count("model.faces"), 1)
        self.assertEqual(names.count("sketch.create"), 1)
        self.assertEqual(names.count("sketch.circle.center"), 1)
        self.assertEqual(names.count("solid.extrude"), 1)

        chamfer_index = names.index("solid.chamfer")
        faces_index = names.index("model.faces")
        sketch_index = names.index("sketch.create")
        self.assertLess(chamfer_index, faces_index)
        self.assertLess(faces_index, sketch_index)

        query = self.commands[faces_index]
        self.assertEqual(query["params"]["body"], "TopSketchAfterChamfer")
        self.assertEqual(
            {
                spec["select"]: spec["where"]
                for spec in query["bind"].values()
            },
            {
                "point": {"plane_normal": [0, 0, 1]},
                "index": {"plane_normal": [0, 0, 1]},
            },
        )
        self.assertTrue(all(
            spec["max"] == "area"
            for spec in query["bind"].values()
        ))

        sketch = self.commands[sketch_index]["params"]
        self.assertEqual(sketch["name"], "Top hole")
        self.assertEqual(
            sketch["plane"]["body"],
            "TopSketchAfterChamfer",
        )

        cut = self.commands[-1]["params"]
        self.assertTrue(cut["through_all"])
        self.assertEqual(cut["direction"], "negative")
        self.assertEqual(cut["operation"], "cut")


if __name__ == "__main__":
    unittest.main()
