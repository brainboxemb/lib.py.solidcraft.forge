"""Native SolidCraft component-drawing contracts."""

import unittest

from scpf import Box, Placement, component
from scpf.assembly import compile_assembly


@component
class DrawingPanel:
    def build(self):
        return Box(40, 30, 10)


class ComponentDrawingTests(unittest.TestCase):
    def test_selected_occurrence_gets_native_standard_drawing(self):
        first = DrawingPanel()
        second = first.copy(placement=Placement(x=50))
        assembly = (first + second).with_drawing(
            second,
            name="Second panel drawing",
        )

        commands = compile_assembly(assembly, "DrawingAssembly")["commands"]

        create_component = next(
            row for row in commands
            if row["command"] == "component.create"
            and row["params"]["name"] == "DrawingPanel"
        )
        self.assertEqual(
            create_component["bind"],
            {
                "$drawingpanel_occurrence_1": "occurrence",
                "$component_1": "component",
            },
        )

        drawing_index = next(
            i for i, row in enumerate(commands)
            if row["command"] == "drawing.create"
        )
        drawing = commands[drawing_index:]
        self.assertEqual(
            drawing[0],
            {
                "command": "drawing.create",
                "params": {
                    "name": "Second panel drawing",
                    "template": "iso-a4-part",
                    "first_sheet_name": "Sheet 1",
                },
                "bind": {
                    "$drawing_1": "id",
                    "$drawing_1_source": {
                        "field": "sources",
                        "where": {"path": None},
                        "select": "id",
                    },
                    "$drawing_1_sheet": {
                        "field": "sheets",
                        "where": {"name": "Sheet 1"},
                        "select": "id",
                    },
                    "$drawing_1_orientation": {
                        "field": "sheets",
                        "where": {"name": "Sheet 1"},
                        "select": "orientation",
                    },
                },
            },
        )
        self.assertEqual(
            drawing[1]["params"],
            {
                "sheet": "$drawing_1_sheet",
                "orientation": "landscape",
                "documents": {
                    "source": "$drawing_1_source",
                    "component": "$component_1",
                },
            },
        )
        self.assertEqual(
            drawing[2],
            {
                "command": "drawing.view.standard",
                "params": {"sheet": "$drawing_1_sheet", "iso": True},
                "bind": {
                    "$drawing_1_front": "view",
                    "$drawing_1_iso": "iso",
                },
            },
        )
        selected = {
            "source": {
                "occurrences": [["$drawingpanel_occurrence_2"]],
            },
        }
        self.assertEqual(
            drawing[3]["params"],
            {"view": "$drawing_1_front", "set": selected},
        )
        self.assertEqual(
            drawing[4]["params"],
            {"view": "$drawing_1_iso", "set": selected},
        )
        self.assertEqual(
            drawing[5],
            {"command": "drawing.close", "params": {}},
        )
        self.assertEqual(
            compile_assembly(assembly, "DrawingAssembly")["artifacts"],
            {
                "drawings": [
                    {
                        "name": "Second panel drawing",
                        "drawing": "$drawing_1",
                        "sheet": "$drawing_1_sheet",
                        "orientation": "$drawing_1_orientation",
                        "pdf": "drawings/Second-panel-drawing.pdf",
                        "png": "drawings/Second-panel-drawing.png",
                    }
                ]
            },
        )

    def test_standalone_component_can_own_a_drawing(self):
        panel = DrawingPanel()
        assembly = panel.with_drawing(name="Panel drawing")
        commands = compile_assembly(assembly, "Panel")["commands"]
        self.assertTrue(any(
            row["command"] == "drawing.create"
            and row["params"]["name"] == "Panel drawing"
            for row in commands
        ))

    def test_a3_template_remains_available_for_complex_parts(self):
        panel = DrawingPanel()
        document = compile_assembly(
            panel.with_drawing(
                name="Large drawing",
                template="iso-a3-part",
            ),
            "Panel",
        )
        create = next(
            row for row in document["commands"]
            if row["command"] == "drawing.create"
        )
        self.assertEqual(create["params"]["template"], "iso-a3-part")

    def test_drawing_intent_is_final_design_state(self):
        first = DrawingPanel()
        second = first.copy(placement=Placement(x=50))
        outsider = DrawingPanel()
        assembly = first + second

        with self.assertRaisesRegex(ValueError, "belong to this assembly"):
            assembly.with_drawing(outsider)
        with self.assertRaisesRegex(ValueError, "already exists"):
            assembly.with_drawing(first, name="Panel").with_drawing(
                second, name="Panel"
            )
        with self.assertRaisesRegex(ValueError, "final assembly"):
            assembly.with_drawing(first) + outsider

    def test_drawing_metadata_is_validated_before_lowering(self):
        panel = DrawingPanel()
        with self.assertRaisesRegex(ValueError, "name must be non-empty"):
            panel.with_drawing(name=" ")
        with self.assertRaisesRegex(ValueError, "template must be non-empty"):
            panel.with_drawing(template="")
        with self.assertRaisesRegex(ValueError, "sheet name must be non-empty"):
            panel.with_drawing(sheet_name="")
        with self.assertRaisesRegex(ValueError, "safe PDF filename"):
            panel.with_drawing(name="...")


if __name__ == "__main__":
    unittest.main()
