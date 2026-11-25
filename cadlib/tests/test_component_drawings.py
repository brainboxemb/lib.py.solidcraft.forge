"""Native SolidCraft component-drawing contracts."""

import unittest

from scpf import (
    Box,
    DrawingDimension,
    DrawingNote,
    DrawingRevision,
    DrawingView,
    Placement,
    component,
)
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
        self.assertNotIn("bind", drawing[1])
        self.assertEqual(
            drawing[2],
            {
                "command": "drawing.inspect",
                "params": {},
                "bind": {
                    "$drawing_1_orientation": {
                        "field": "sheets",
                        "where": {"name": "Sheet 1"},
                        "select": "orientation",
                    },
                },
            },
        )
        self.assertEqual(
            drawing[3],
            {
                "command": "drawing.view.standard",
                "params": {
                    "sheet": "$drawing_1_sheet",
                    "iso": True,
                    "gap_mm": 20.0,
                },
                "bind": {
                    "$drawing_1_front": "view",
                    "$drawing_1_top": "top",
                    "$drawing_1_right": "right",
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
            drawing[4]["params"],
            {"view": "$drawing_1_front", "set": selected},
        )
        self.assertEqual(
            drawing[5]["params"],
            {"view": "$drawing_1_iso", "set": selected},
        )
        self.assertEqual(
            drawing[6],
            {"command": "drawing.inspect", "params": {}},
        )
        self.assertEqual(
            drawing[7],
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
                        "inspect": "drawings/Second-panel-drawing.json",
                        "expected": {
                            "orientation": "landscape",
                            "view_count": 4,
                            "dimension_count": 0,
                            "note_count": 0,
                            "properties": {},
                            "title_block": {},
                        },
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
        sheet = next(
            row for row in document["commands"]
            if row["command"] == "drawing.sheet.set"
        )
        self.assertEqual(sheet["params"]["orientation"], "landscape")

    def test_consumer_can_author_layout_metadata_notes_and_dimensions(self):
        panel = DrawingPanel()
        document = compile_assembly(
            panel.with_drawing(
                name="Panel drawing",
                scale="2:1",
                gap_mm=12,
                views={
                    "front": DrawingView(at=(65, 120)),
                    "top": DrawingView(at=(65, 55)),
                    "right": DrawingView(at=(135, 120)),
                    "iso": DrawingView(
                        at=(220, 125),
                        scale="1:1",
                        visual_style="shaded",
                    ),
                },
                properties={
                    "project": "Drawing qualification",
                    "part_number": "DWG-001",
                    "author": "Forge",
                    "organization": "brainboxemb",
                    "description": "Panel engineering drawing",
                },
                title_block={
                    "title": "Panel",
                    "document_status": "Qualification",
                    "department": "Engineering",
                },
                revision=DrawingRevision(
                    revision="A",
                    description="Initial drawing",
                    designer="Forge",
                    checker="CI",
                    date="2026-11-25",
                ),
                notes=(
                    DrawingNote(
                        "1. ALL DIMENSIONS IN MM\n2. BREAK SHARP EDGES",
                        at=(170, 70),
                        cap_mm=2.5,
                    ),
                ),
                dimensions=(
                    DrawingDimension.linear(
                        "front",
                        (-20, -15, 0),
                        (20, -15, 0),
                        direction="horizontal",
                        offset_mm=12,
                    ),
                    DrawingDimension.radial(
                        "top",
                        (5, 0, 10),
                        diameter=True,
                        override_text="2× {value} THRU",
                        line_through_mm=(80, 75),
                    ),
                ),
            ),
            "Panel",
        )
        commands = document["commands"]

        sheet = next(
            row for row in commands
            if row["command"] == "drawing.sheet.set"
        )
        self.assertEqual(
            sheet["params"]["title_block_overrides"],
            {
                "title": "Panel",
                "document_status": "Qualification",
                "department": "Engineering",
            },
        )

        properties = next(
            row for row in commands
            if row["command"] == "drawing.properties.set"
        )
        self.assertEqual(
            properties["params"]["values"]["part_number"],
            "DWG-001",
        )

        revision = next(
            row for row in commands
            if row["command"] == "drawing.revision.add"
        )
        self.assertEqual(revision["params"]["set"]["revision"], "A")
        self.assertEqual(revision["params"]["set"]["checker"], "CI")

        standard = next(
            row for row in commands
            if row["command"] == "drawing.view.standard"
        )
        self.assertEqual(standard["params"]["scale"], "2:1")
        self.assertEqual(standard["params"]["gap_mm"], 12.0)

        layout = [
            row for row in commands
            if row["command"] == "drawing.view.edit"
            and "place" in row["params"]["set"]
        ]
        self.assertEqual(len(layout), 4)
        iso = next(
            row for row in layout
            if row["params"]["view"] == "$drawing_1_iso"
        )
        self.assertEqual(iso["params"]["set"]["scale"], "1:1")
        self.assertEqual(
            iso["params"]["set"]["visual_style"],
            "shaded",
        )

        dimensions = [
            row for row in commands
            if row["command"] == "drawing.dimension.add"
        ]
        self.assertEqual(len(dimensions), 2)
        self.assertEqual(
            dimensions[0]["params"]["kind"]["linear"]["a"]["path"],
            ["$drawingpanel"],
        )
        face_dimension = DrawingDimension.faces(
            "front",
            (-20, 0, 5),
            (20, 0, 5),
            direction="horizontal",
        )
        self.assertEqual(face_dimension.kind, "faces")
        self.assertEqual(face_dimension.a, (-20.0, 0.0, 5.0))
        self.assertEqual(face_dimension.b, (20.0, 0.0, 5.0))

        self.assertEqual(
            dimensions[1]["params"]["override_text"],
            "2× {value} THRU",
        )
        self.assertEqual(
            dimensions[1]["params"]["line_through_mm"],
            [80.0, 75.0],
        )

        note = next(
            row for row in commands
            if row["command"] == "drawing.note.add"
        )
        self.assertEqual(note["params"]["anchor"], {"sheet": "$drawing_1_sheet"})
        self.assertIn("ALL DIMENSIONS IN MM", note["params"]["content"])

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
        with self.assertRaisesRegex(ValueError, "unsupported drawing view"):
            panel.with_drawing(views={"rear": DrawingView(at=(1, 2))})
        with self.assertRaisesRegex(
            ValueError,
            "visual_style currently supports only 'shaded'",
        ):
            DrawingView(visual_style="wireframe")
        with self.assertRaisesRegex(ValueError, "unsupported drawing property"):
            panel.with_drawing(properties={"owner": "x"})
        with self.assertRaisesRegex(ValueError, "dimension view"):
            DrawingDimension.linear("rear", (0, 0, 0), (1, 0, 0))


if __name__ == "__main__":
    unittest.main()
