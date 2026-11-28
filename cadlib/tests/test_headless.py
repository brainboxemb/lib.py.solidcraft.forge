"""Headless replay transport tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scpf.headless import (
    HeadlessReplayError,
    _active_component_after,
    _active_drawing_after,
    _active_sketch_after,
    _phase_commands,
    run_document,
)
from scpf.replay import apply_bindings, validate_replay_document


class ScriptedSolidCraftTransport:
    """Strict test transport: return only responses declared by the test."""

    def __init__(self, *phases):
        self._phases = list(phases)
        self.calls = []

    def run_phase(
        self,
        commands,
        *,
        phase_index,
        previous,
        save,
        export,
        work,
    ):
        if not self._phases:
            raise AssertionError(
                f"unexpected SolidCraft replay phase {phase_index}: {commands!r}"
            )
        script = self._phases.pop(0)
        expected = [step["command"] for step in script]
        actual = [item["command"] for item in commands]
        if actual != expected:
            raise AssertionError(
                f"unexpected SolidCraft commands in phase {phase_index}: "
                f"expected {expected!r}, got {actual!r}"
            )
        for item, step in zip(commands, script):
            if "params" in step and item.get("params", {}) != step["params"]:
                raise AssertionError(
                    f"unexpected params for {item['command']}: "
                    f"expected {step['params']!r}, "
                    f"got {item.get('params', {})!r}"
                )
        self.calls.append({
            "phase_index": phase_index,
            "commands": commands,
            "previous": previous,
            "save": save,
            "export": export,
            "work": work,
        })
        return [step.get("result", {}) for step in script]

    def assert_complete(self):
        if self._phases:
            raise AssertionError(
                f"{len(self._phases)} scripted SolidCraft phase(s) were unused"
            )


class HeadlessTransportInjectionTests(unittest.TestCase):
    def test_scripted_transport_replays_bindings_and_restores_context(self):
        document = {
            "format": "scpf-replay",
            "version": 2,
            "commands": [
                {
                    "command": "component.create",
                    "params": {"name": "Panel"},
                },
                {
                    "command": "sketch.create",
                    "params": {"name": "Top"},
                },
                {
                    "command": "model.faces",
                    "params": {"body": "Panel"},
                    "bind": {
                        "$top_point": {
                            "field": "faces",
                            "where": {"plane_normal": [0, 0, 1]},
                            "max": "area",
                            "select": "point",
                        },
                    },
                },
                {
                    "command": "sketch.circle.center",
                    "params": {
                        "center": "$top_point",
                        "diameter": 4,
                    },
                },
            ],
        }
        transport = ScriptedSolidCraftTransport(
            [
                {
                    "command": "component.create",
                    "result": {"component": 1},
                },
                {
                    "command": "sketch.create",
                    "result": {"sketch": 7},
                },
                {
                    "command": "model.faces",
                    "result": {
                        "faces": [{
                            "index": 5,
                            "name": "F5",
                            "area": 1200.0,
                            "point": [0.0, 0.0, 10.0],
                            "plane_normal": [0.0, 0.0, 1.0],
                        }],
                    },
                },
            ],
            [
                {
                    "command": "component.activate",
                    "params": {"component": "Panel"},
                },
                {
                    "command": "sketch.edit",
                    "params": {"sketch": 7},
                },
                {
                    "command": "sketch.circle.center",
                    "params": {
                        "center": [0.0, 0.0, 10.0],
                        "diameter": 4,
                    },
                    "result": {"curves": ["circle1"]},
                },
            ],
        )

        with tempfile.TemporaryDirectory(prefix="scpf-scripted-") as tmp:
            with patch("scpf.headless.subprocess.run") as subprocess_run:
                result = run_document(
                    document,
                    save=Path(tmp) / "model.sc",
                    work_dir=Path(tmp) / "work",
                    _transport=transport,
                )

        subprocess_run.assert_not_called()
        transport.assert_complete()
        self.assertEqual(result["completed"], 4)
        self.assertEqual(result["variables"]["$top_point"], [0.0, 0.0, 10.0])
        self.assertEqual(len(result["results"]), 4)
        self.assertEqual(
            [row["command"] for row in transport.calls[1]["commands"]],
            ["component.activate", "sketch.edit", "sketch.circle.center"],
        )

    def test_scripted_transport_fails_closed_on_unexpected_command(self):
        transport = ScriptedSolidCraftTransport([
            {"command": "solid.box", "result": {}},
        ])
        document = {
            "commands": [{
                "command": "solid.cylinder",
                "params": {"diameter": 4, "height": 8},
            }],
        }

        with tempfile.TemporaryDirectory(prefix="scpf-scripted-") as tmp:
            with self.assertRaisesRegex(
                AssertionError,
                "unexpected SolidCraft commands",
            ):
                run_document(
                    document,
                    save=Path(tmp) / "model.sc",
                    _transport=transport,
                )

    def test_scripted_transport_result_cardinality_is_still_validated(self):
        class MissingResultTransport:
            def run_phase(self, commands, **kwargs):
                return []

        document = {
            "commands": [{
                "command": "solid.box",
                "params": {"length": 1, "width": 1, "height": 1},
            }],
        }

        with tempfile.TemporaryDirectory(prefix="scpf-scripted-") as tmp:
            with self.assertRaisesRegex(
                HeadlessReplayError,
                "one result per native phase command",
            ):
                run_document(
                    document,
                    save=Path(tmp) / "model.sc",
                    _transport=MissingResultTransport(),
                )


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
