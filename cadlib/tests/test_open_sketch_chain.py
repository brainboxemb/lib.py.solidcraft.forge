"""Contracts for reusable open connected Sketch chains."""

import unittest

from scpf import Anchor, Box, Parameter, Sketch
from scpf.compiler import compile_model


class OpenSketchChainTests(unittest.TestCase):
    def test_open_chain_lowers_line_tangent_arc_line_with_private_native_ids(self):
        length = Parameter("length", 40)
        end_height = Parameter("end_height", 30)

        with Sketch(name="Contour", plane="XY") as sketch:
            chain = sketch.chain(start=(0, 0))
            chain.line_to((length, 0))
            chain.tangent_arc_to((50, 10))
            chain.line_to((50, end_height))
            contour = chain.finish()

        document = compile_model(contour, "ContourPath")
        commands = document["commands"]
        geometry = [
            row for row in commands
            if row["command"] != "parameters.add"
        ]
        self.assertEqual(
            [row["command"] for row in geometry],
            [
                "sketch.create",
                "sketch.line",
                "sketch.arc.tangent",
                "sketch.line",
                "sketch.finish",
            ],
        )

        first = geometry[1]["params"]
        self.assertEqual(first["points"], [[0, 0], ["length", 0]])
        self.assertEqual(first["ids"], ["l1"])
        self.assertTrue(first["connect"])

        tangent = geometry[2]["params"]
        self.assertEqual(tangent["start"], "l1.end")
        self.assertEqual(tangent["curve"], "l1")
        self.assertEqual(tangent["end"], [50, 10])

        second = geometry[3]["params"]
        self.assertEqual(
            second["points"],
            [[50, 10], [50, "end_height"]],
        )
        self.assertEqual(second["ids"], ["l2"])
        self.assertTrue(second["connect"])

        units = {
            row["params"]["name"]: row["params"]["unit"]
            for row in commands
            if row["command"] == "parameters.add"
        }
        self.assertEqual(units, {"length": "mm", "end_height": "mm"})

    def test_open_chain_supports_standalone_plane_offset(self):
        with Sketch(name="OffsetPath", plane="XZ", offset=12) as sketch:
            chain = sketch.chain(start=(0, 0))
            chain.line_to((20, 0))
            path = chain.finish()

        create = compile_model(path, "OffsetPath")["commands"][0]["params"]
        self.assertEqual(create["plane"], "XZ")
        self.assertEqual(create["offset"], 12)
        self.assertEqual(create["name"], "OffsetPath")

    def test_open_chain_authoring_is_explicit_and_stays_open(self):
        with Sketch(name="TangentRule", plane="XY") as sketch:
            chain = sketch.chain(start=(0, 0))
            with self.assertRaisesRegex(ValueError, "preceding line"):
                chain.tangent_arc_to((10, 10))
            chain.line_to((10, 0))
            arc_end = Parameter("arc_end", 20)
            with self.assertRaisesRegex(ValueError, "fixed numeric geometry"):
                chain.tangent_arc_to((arc_end, 10))
            chain.tangent_arc_to((20, 10))
            with self.assertRaisesRegex(ValueError, "preceding line"):
                chain.tangent_arc_to((30, 20))
            chain.line_to((30, 10))
            chain.finish()

        with Sketch(name="MustStayOpen", plane="XY") as sketch:
            chain = sketch.chain(start=(0, 0))
            chain.line_to((10, 0))
            chain.line_to((0, 0))
            with self.assertRaisesRegex(ValueError, "must remain open"):
                chain.finish()
            chain.line_to((0, 10))
            chain.finish()

    def test_unfinished_or_unsupported_chain_context_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be finished"):
            with Sketch(name="Unfinished", plane="XY") as sketch:
                chain = sketch.chain(start=(0, 0))
                chain.line_to((10, 0))

        base = Box(40, 30, 5, anchor=Anchor.BOTTOM)
        with Sketch(name="Attached", on=base, parent=Anchor.TOP) as sketch:
            with self.assertRaisesRegex(ValueError, "standalone"):
                sketch.chain(start=(0, 0))
            # Keep the existing Sketch context itself valid.
            from scpf import Circle2D
            Circle2D(d=5)

        with Sketch(name="Origin", plane="XY", origin=(0, 0, 0)) as sketch:
            with self.assertRaisesRegex(ValueError, "explicit Sketch origin"):
                sketch.chain(start=(0, 0))
            from scpf import Circle2D
            Circle2D(d=5)


if __name__ == "__main__":
    unittest.main()
