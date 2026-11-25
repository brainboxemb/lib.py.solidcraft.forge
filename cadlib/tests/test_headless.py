"""Headless replay transport tests."""

import unittest

from scpf.headless import (
    HeadlessReplayError,
    _active_component_after,
    _active_drawing_after,
    _active_sketch_after,
    _phase_commands,
)
from scpf.replay import apply_bindings, validate_replay_document


class HeadlessSketchReplayTests(unittest.TestCase):
    def test_next_phase_reopens_active_sketch_by_native_feature_id(self):
        chunk = [{
            "command": "sketch.pattern.rectangular",
            "params": {
                "entities": "$seed_curves",
                "count": 3,
                "spacing": 20,
            },
        }]
        native, prefix = _phase_commands(
            chunk,
            {"$seed_curves": ["circle1"]},
            17,
        )

        self.assertEqual(prefix, 1)
        self.assertEqual(
            native[0],
            {"command": "sketch.edit", "params": {"sketch": 17}},
        )
        self.assertEqual(native[1]["params"]["entities"], ["circle1"])

    def test_create_result_opens_and_finish_closes_tracked_sketch(self):
        active = _active_sketch_after(
            [
                {"command": "sketch.create", "params": {"name": "Pattern"}},
                {"command": "sketch.circle.center", "params": {"center": [0, 0]}},
            ],
            [
                {"sketch": 23, "name": "Pattern"},
                {"curves": ["circle1"]},
            ],
            None,
        )
        self.assertEqual(active, 23)

        active = _active_sketch_after(
            [{"command": "sketch.finish", "params": {}}],
            [{}],
            active,
        )
        self.assertIsNone(active)

    def test_create_must_return_native_sketch_id(self):
        with self.assertRaisesRegex(
            HeadlessReplayError,
            "did not return a sketch id",
        ):
            _active_sketch_after(
                [{"command": "sketch.create", "params": {"name": "Pattern"}}],
                [{"name": "Pattern"}],
                None,
            )


class HeadlessComponentReplayTests(unittest.TestCase):
    def test_next_phase_reactivates_component_before_native_commands(self):
        chunk = [{
            "command": "solid.cylinder",
            "params": {
                "diameter": 4,
                "height": 4,
                "operation": "join",
                "targets": ["Panel"],
            },
        }]
        native, prefix = _phase_commands(
            chunk,
            {},
            None,
            "Panel",
        )

        self.assertEqual(prefix, 1)
        self.assertEqual(
            native[0],
            {
                "command": "component.activate",
                "params": {"component": "Panel"},
            },
        )
        self.assertEqual(native[1]["command"], "solid.cylinder")

    def test_component_restore_precedes_sketch_restore(self):
        chunk = [{
            "command": "sketch.circle.center",
            "params": {"center": [0, 0], "diameter": 4},
        }]
        native, prefix = _phase_commands(
            chunk,
            {},
            17,
            "Panel",
        )

        self.assertEqual(prefix, 2)
        self.assertEqual(
            [row["command"] for row in native[:2]],
            ["component.activate", "sketch.edit"],
        )
        self.assertEqual(
            native[0]["params"]["component"],
            "Panel",
        )
        self.assertEqual(native[1]["params"]["sketch"], 17)

    def test_component_create_and_activate_update_tracked_context(self):
        active = _active_component_after(
            [
                {
                    "command": "component.create",
                    "params": {"name": "Panel"},
                },
            ],
            [{"component": 1, "occurrence": 2}],
            None,
        )
        self.assertEqual(active, "Panel")

        active = _active_component_after(
            [
                {
                    "command": "component.activate",
                    "params": {"component": "root"},
                },
            ],
            [{}],
            active,
        )
        self.assertIsNone(active)

    def test_component_create_requires_usable_identity(self):
        with self.assertRaisesRegex(
            HeadlessReplayError,
            "no usable component target",
        ):
            _active_component_after(
                [
                    {
                        "command": "component.create",
                        "params": {},
                    },
                ],
                [{}],
                None,
            )


class HeadlessDrawingReplayTests(unittest.TestCase):
    def test_next_phase_reopens_active_drawing_before_native_commands(self):
        chunk = [{
            "command": "drawing.sheet.set",
            "params": {"sheet": "sheet-1", "line_group": 0.5},
        }]
        native, prefix = _phase_commands(
            chunk,
            {},
            None,
            None,
            "drawing-1",
        )
        self.assertEqual(prefix, 1)
        self.assertEqual(
            native[0],
            {
                "command": "drawing.open",
                "params": {"drawing": "drawing-1"},
            },
        )
        self.assertEqual(native[1]["command"], "drawing.sheet.set")

    def test_create_open_and_close_update_tracked_drawing(self):
        active = _active_drawing_after(
            [{"command": "drawing.create", "params": {"name": "Part"}}],
            [{"id": "drawing-1", "name": "Part"}],
            None,
        )
        self.assertEqual(active, "drawing-1")
        active = _active_drawing_after(
            [{"command": "drawing.open", "params": {"drawing": "drawing-2"}}],
            [{"id": "drawing-2"}],
            active,
        )
        self.assertEqual(active, "drawing-2")
        active = _active_drawing_after(
            [{"command": "drawing.close", "params": {}}],
            [{}],
            active,
        )
        self.assertIsNone(active)

    def test_drawing_create_requires_usable_identity(self):
        with self.assertRaisesRegex(
            HeadlessReplayError,
            "did not return a drawing id",
        ):
            _active_drawing_after(
                [{"command": "drawing.create", "params": {"name": "Part"}}],
                [{"name": "Part"}],
                None,
            )


class ReplaySelectorTests(unittest.TestCase):
    def test_numeric_vector_selector_tolerates_kernel_float_noise(self):
        items = [{
            "command": "model.faces",
            "params": {"body": "Plate"},
            "bind": {
                "$top_point": {
                    "field": "faces",
                    "where": {"plane_normal": [0, 0, 1]},
                    "max": "area",
                    "select": "point",
                },
            },
        }]
        results = [{
            "faces": [
                {
                    "area": 7000.0,
                    "plane_normal": [2e-12, -3e-12, 0.9999999999997],
                    "point": [0.0, 0.0, 10.0],
                },
                {
                    "area": 7000.0,
                    "plane_normal": [0.0, 0.0, -1.0],
                    "point": [0.0, 0.0, 0.0],
                },
            ],
        }]
        variables = {}

        bindings = apply_bindings(items, results, variables)

        self.assertEqual(variables["$top_point"], [0.0, 0.0, 10.0])
        self.assertEqual(
            bindings,
            [{"$top_point": [0.0, 0.0, 10.0]}],
        )

    def test_boundary_selector_returns_native_edge_refs(self):
        items = [
            {
                "command": "model.faces",
                "params": {"body": "Plate"},
                "bind": {
                    "$face": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                    },
                },
            },
            {
                "command": "model.edges",
                "params": {"body": "Plate"},
                "bind": {
                    "$edges": {
                        "field": "edges",
                        "boundary_of": "$face",
                        "body": "Plate",
                    },
                },
            },
        ]
        validate_replay_document({
            "format": "scpf-replay",
            "version": 2,
            "commands": items,
        })
        variables = {}
        apply_bindings(
            [items[0]],
            [{
                "faces": [{
                    "index": 5,
                    "name": "F5",
                    "area": 1200.0,
                    "point": [0.0, 0.0, 10.0],
                    "plane_normal": [0.0, 0.0, 1.0],
                }],
            }],
            variables,
        )
        apply_bindings(
            [items[1]],
            [{
                "edges": [
                    {
                        "index": 1,
                        "name": "F5|front",
                        "start": [-20, -15, 10],
                        "end": [20, -15, 10],
                        "mid": [0, -15, 10],
                    },
                    {
                        "index": 2,
                        "name": "right|F5",
                        "start": [20, -15, 10],
                        "end": [20, 15, 10],
                        "mid": [20, 0, 10],
                    },
                    {
                        "index": 9,
                        "name": "right|back",
                        "start": [20, 15, 0],
                        "end": [20, 15, 10],
                        "mid": [20, 15, 5],
                    },
                ],
            }],
            variables,
        )
        self.assertEqual(
            variables["$edges"],
            [
                {"body": "Plate", "index": 1},
                {"body": "Plate", "index": 2},
            ],
        )

    def test_boundary_selector_prepends_and_deduplicates_face_edges(self):
        items = [{
            "command": "model.edges",
            "params": {"body": "Plate"},
            "bind": {
                "$all_edges": {
                    "field": "edges",
                    "boundary_of": "$bottom_face",
                    "body": "Plate",
                    "prepend": "$top_edges",
                },
            },
        }]
        variables = {
            "$bottom_face": {
                "point": [0, 0, 0],
                "plane_normal": [0, 0, -1],
            },
            "$top_edges": [
                {"body": "Plate", "index": 1},
                {"body": "Plate", "index": 7},
            ],
        }
        apply_bindings(
            items,
            [{
                "edges": [
                    {
                        "index": 7,
                        "name": "bottom|front",
                        "start": [-20, -15, 0],
                        "end": [20, -15, 0],
                        "mid": [0, -15, 0],
                    },
                    {
                        "index": 8,
                        "name": "right|bottom",
                        "start": [20, -15, 0],
                        "end": [20, 15, 0],
                        "mid": [20, 0, 0],
                    },
                ],
            }],
            variables,
        )
        self.assertEqual(
            variables["$all_edges"],
            [
                {"body": "Plate", "index": 1},
                {"body": "Plate", "index": 7},
                {"body": "Plate", "index": 8},
            ],
        )

    def test_numeric_vector_selector_rejects_a_different_direction(self):
        items = [{
            "command": "model.faces",
            "params": {"body": "Plate"},
            "bind": {
                "$top_point": {
                    "field": "faces",
                    "where": {"plane_normal": [0, 0, 1]},
                    "max": "area",
                    "select": "point",
                },
            },
        }]
        results = [{
            "faces": [{
                "area": 7000.0,
                "plane_normal": [0.0, 0.0, 0.999],
                "point": [0.0, 0.0, 10.0],
            }],
        }]

        with self.assertRaisesRegex(ValueError, "matched no 'faces' records"):
            apply_bindings(items, results, {})



if __name__ == "__main__":
    unittest.main()
