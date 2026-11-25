"""Command/replay contract for the #845 contour-flange recess fixture."""

import unittest
from pathlib import Path

from scpf.replay import replay_chunks
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-contour-flange-recess/scpf/model.py"


class SheetContourFlangeRecessContractTests(unittest.TestCase):
    def test_exact_broad_face_recess_is_preserved(self):
        document = run_script(MODEL)
        self.assertEqual(document["format"], "scpf-replay")
        self.assertEqual(document["version"], 2)

        commands = document["commands"]

        face = next(row for row in commands if row["command"] == "model.faces")
        self.assertEqual(face["params"], {"body": "SheetContourFlangeRecess"})
        self.assertEqual(
            face["bind"]["$face_point_1"]["where"],
            {"plane_normal": [0, 0, 1]},
        )
        self.assertEqual(face["bind"]["$face_point_1"]["max"], "area")

        sketch = next(
            row for row in commands
            if row["command"] == "sketch.create"
            and row["params"].get("name") == "Broad face recess"
        )
        self.assertEqual(
            sketch["params"]["plane"],
            {
                "face": "$face_point_1",
                "body": "SheetContourFlangeRecess",
                "index": "$face_index_1",
            },
        )

        circle = next(
            row for row in commands
            if row["command"] == "sketch.circle.center"
        )
        self.assertEqual(circle["params"]["center"], [0.0, 37.5])
        self.assertEqual(circle["params"]["diameter"], 12.5)

        cut = next(
            row for row in commands
            if row["command"] == "solid.extrude"
            and row["params"].get("name") == "Broad face recess"
        )
        self.assertEqual(cut["params"]["operation"], "cut")
        self.assertEqual(cut["params"]["targets"], ["SheetContourFlangeRecess"])
        self.assertTrue(cut["params"]["through_all"])
        self.assertEqual(cut["params"]["direction"], "negative")

    def test_face_binding_is_a_replay_phase_boundary(self):
        commands = run_script(MODEL)["commands"]
        chunks = replay_chunks(commands)

        face_chunk = next(
            index
            for index, chunk in enumerate(chunks)
            if any(row["command"] == "model.faces" for row in chunk)
        )
        self.assertLess(face_chunk + 1, len(chunks))

        following = chunks[face_chunk + 1]
        self.assertEqual(following[0]["command"], "sketch.create")
        self.assertEqual(following[0]["params"]["name"], "Broad face recess")
        self.assertIn(
            "solid.extrude",
            [row["command"] for row in following],
        )


if __name__ == "__main__":
    unittest.main()
