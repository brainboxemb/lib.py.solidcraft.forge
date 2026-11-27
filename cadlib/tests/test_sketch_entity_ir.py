"""Contracts for support-independent semantic Sketch entity IR."""

import unittest

from scpf import (
    Anchor,
    Axis,
    Box,
    Circle2D,
    Depth,
    Parameter,
    Sketch,
)
from scpf.backends.solidcraft import (
    _solidcraft_open_chain_commands,
    _solidcraft_sketch_graph_commands,
)
from scpf.compiler import ModelError, _compile_shape_legacy_with_dependencies
from scpf.core import Text2D
from scpf.ir import (
    ConnectedProfileIR,
    LegacyShapeIR,
    OpenChainIR,
    ParameterIR,
    SketchEntityGraphIR,
    SketchEntityRefIR,
    SketchMirrorIR,
    SketchRectangularPatternIR,
    TextEntityIR,
    normalize_shape,
    normalize_sketch_entities,
)
from scpf.sketches import compile_open_chain


class SketchEntityIRTests(unittest.TestCase):
    def test_connected_line_arc_profile_is_semantic_graph(self):
        length = Parameter("profile_length", 20)
        with Sketch(name="Connected", plane="XY") as sketch:
            profile = sketch.profile(start=(0, 0))
            profile.line_to((length, 0))
            profile.arc_center_to(
                (0, 0),
                center=(length / 2, 0),
                clockwise=False,
            )
            authored = profile.close()

        graph = normalize_sketch_entities(sketch)
        self.assertIsInstance(graph, SketchEntityGraphIR)
        self.assertEqual(len(graph.entities), 1)
        semantic = graph.entities[0]
        self.assertIsInstance(semantic, ConnectedProfileIR)
        self.assertEqual(
            [segment.kind for segment in semantic.segments],
            ["line", "arc_center_point"],
        )
        self.assertIs(semantic.segments[0].end[0], length)

        shape = sketch.extrude(5)
        legacy = _compile_shape_legacy_with_dependencies(
            shape,
            "ConnectedProfile",
        )[0]["commands"]
        expected = [
            row
            for row in legacy
            if row["command"].startswith("sketch.")
            and row["command"] not in {"sketch.create", "sketch.finish"}
        ]
        self.assertEqual(
            _solidcraft_sketch_graph_commands(graph),
            expected,
        )

    def test_open_line_tangent_chain_is_semantic_graph(self):
        span = Parameter("chain_span", 20)
        with Sketch(name="FoldPath", plane="XY") as sketch:
            chain = (
                sketch.chain(start=(0, 0))
                .line_to((span, 0))
                .tangent_arc_to((30, 10))
                .finish()
            )

        graph = normalize_sketch_entities(sketch)
        self.assertEqual(graph.entities, ())
        self.assertEqual(len(graph.open_chains), 1)
        semantic = graph.open_chains[0]
        self.assertIsInstance(semantic, OpenChainIR)
        self.assertEqual(
            [segment.kind for segment in semantic.segments],
            ["line", "arc_tangent"],
        )
        self.assertIs(semantic.segments[0].end[0], span)

        legacy, _meta = compile_open_chain(chain)
        expected = [
            row
            for row in legacy
            if row["command"] not in {"sketch.create", "sketch.finish"}
        ]
        self.assertEqual(
            _solidcraft_open_chain_commands(semantic),
            expected,
        )

    def test_text_entity_retains_symbolic_height_and_insertion(self):
        height = Parameter("label_height", 8)
        board = Box(60, 40, 4, anchor=Anchor.BOTTOM)
        with Sketch(
            name="Label",
            on=board,
            parent=Anchor.TOP,
        ) as sketch:
            text = Text2D("A", height=height)
            sketch.add(text, offset=(5, -3))

        graph = normalize_sketch_entities(sketch)
        self.assertEqual(len(graph.entities), 1)
        semantic = graph.entities[0]
        self.assertIsInstance(semantic, TextEntityIR)
        self.assertEqual(semantic.text, "A")
        self.assertIs(semantic.height, height)
        self.assertEqual(semantic.position, (5, -3))

        typed_rows = _solidcraft_sketch_graph_commands(graph)
        cut = sketch.extrude(Depth.THROUGH_ALL)
        legacy = _compile_shape_legacy_with_dependencies(
            board - cut,
            "TextBoard",
        )[0]["commands"]
        expected = [
            row
            for row in legacy
            if row["command"].startswith("sketch.")
            and row["command"] not in {"sketch.create", "sketch.finish"}
        ]
        self.assertEqual(typed_rows, expected)

    def test_pattern_mirror_graph_uses_semantic_source_refs_and_roles(self):
        count = Parameter("sketch_count", 3)
        spacing = Parameter("sketch_spacing", 14)
        board = Box(100, 60, 4, anchor=Anchor.BOTTOM)
        with Sketch(
            name="Pattern",
            on=board,
            parent=Anchor.TOP,
        ) as sketch:
            circle = Circle2D(d=6)
            pattern = sketch.rectangular_pattern(
                circle,
                count=count,
                spacing=spacing,
                direction=Axis.X,
            )
            sketch.mirror(pattern, axis=Axis.Y)

        graph = normalize_sketch_entities(sketch)
        self.assertEqual(len(graph.entities), 1)
        self.assertEqual(len(graph.operations), 2)
        rectangular, mirror = graph.operations
        self.assertIsInstance(rectangular, SketchRectangularPatternIR)
        self.assertEqual(
            rectangular.source,
            SketchEntityRefIR("entity", 0),
        )
        self.assertIs(rectangular.count, count)
        self.assertIs(rectangular.spacing, spacing)
        self.assertIsInstance(mirror, SketchMirrorIR)
        self.assertEqual(
            mirror.source,
            SketchEntityRefIR("operation", 0),
        )
        self.assertEqual(mirror.axis, "y")

        cut = sketch.extrude(Depth.THROUGH_ALL)
        shape = board - cut
        normalized = normalize_shape(shape)
        self.assertIsInstance(normalized.root, LegacyShapeIR)
        self.assertEqual(
            normalized.parameters,
            (
                ParameterIR("sketch_count", 3, roles=("count",)),
                ParameterIR("sketch_spacing", 14, roles=("length",)),
            ),
        )

        legacy = _compile_shape_legacy_with_dependencies(
            shape,
            "PatternBoard",
        )[0]["commands"]
        expected = [
            row
            for row in legacy
            if row["command"].startswith("sketch.")
            and row["command"] not in {"sketch.create", "sketch.finish"}
        ]
        self.assertEqual(
            _solidcraft_sketch_graph_commands(graph),
            expected,
        )

    def test_connected_profile_pattern_is_typed_but_backend_fails_closed(self):
        board = Box(80, 50, 4, anchor=Anchor.BOTTOM)
        with Sketch(
            name="UnsupportedPattern",
            on=board,
            parent=Anchor.TOP,
        ) as sketch:
            builder = sketch.profile(start=(0, 0))
            builder.line_to((20, 0))
            builder.line_to((20, 10))
            builder.line_to((0, 10))
            builder.line_to((0, 0))
            profile = builder.close()
            sketch.rectangular_pattern(
                profile,
                count=2,
                spacing=25,
            )

        graph = normalize_sketch_entities(sketch)
        self.assertIsInstance(graph.entities[0], ConnectedProfileIR)
        self.assertIsInstance(
            graph.operations[0],
            SketchRectangularPatternIR,
        )
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support connected profiles",
        ):
            _solidcraft_sketch_graph_commands(graph)


if __name__ == "__main__":
    unittest.main()
