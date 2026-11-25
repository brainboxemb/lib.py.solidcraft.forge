@component
class SamplePlate:
    """Reusable part definition; drawing intent is deliberately not stored here."""

    width = 80
    depth = 50
    thickness = 8

    def build(self):
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(self.width, self.depth)
        plate = sketch.extrude(self.thickness)
        plate = plate.fillet(6, edges=Edges.VERTICAL)

        with Sketch(name="Holes", on=plate, parent=Anchor.TOP) as holes:
            holes.add(
                Circle2D(d=8),
                offset=(-half(self.width - 24), 0),
            )
        source_cut = holes.extrude(Depth.THROUGH_ALL)
        plate = plate - source_cut
        plate = plate.rectangular_pattern(
            source_cut,
            count=2,
            spacing=self.width - 24,
            direction=Axis.X,
        )

        boss = Cylinder(d=24, h=14).attach(
            plate,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )
        plate = plate + boss

        bore = Hole(d=12, depth=Depth.THROUGH_ALL).attach(
            plate,
            parent=Anchor.TOP,
        )
        return plate + bore


def sample_plate_drawing():
    """Consumer-grade native engineering drawing authored through public Forge API."""
    plate = SamplePlate()
    return plate.with_drawing(
        name="Sample Plate Drawing",
        scale="1:1",
        gap_mm=14,
        views={
            "front": DrawingView(at=(62, 128)),
            "top": DrawingView(at=(62, 62)),
            "right": DrawingView(at=(137, 128)),
            "iso": DrawingView(
                at=(220, 128),
                scale="1:1",
                visual_style="shaded",
            ),
        },
        properties={
            "project": "Forge drawing qualification",
            "part_number": "SCPF-DWG-001",
            "author": "Forge",
            "organization": "brainboxemb",
            "description": "Sample plate engineering drawing",
        },
        title_block={
            "title": "Sample Plate",
            "identification_number": "SCPF-DWG-001",
            "material": "Qualification material",
            "finish": "As modelled",
            "document_status": "Qualification",
            "department": "Engineering",
        },
        revision=DrawingRevision(
            revision="A",
            description="Initial qualified drawing",
            designer="Forge",
            checker="CI",
            date="2026-11-25",
        ),
        notes=(
            DrawingNote(
                "NOTES\n1. ALL DIMENSIONS IN MM.\n2. BREAK SHARP EDGES.",
                at=(156, 88),
                cap_mm=2.5,
            ),
        ),
        dimensions=(
            DrawingDimension.faces(
                "front",
                (-40, 0, 4),
                (40, 0, 4),
                direction="horizontal",
                offset_mm=12,
                decimals=0,
            ),
            DrawingDimension.faces(
                "front",
                (30, 20, 0),
                (30, 20, 8),
                direction="vertical",
                offset_mm=10,
                decimals=0,
            ),
            DrawingDimension.faces(
                "top",
                (-40, 0, 4),
                (40, 0, 4),
                direction="horizontal",
                offset_mm=12,
                decimals=0,
            ),
            DrawingDimension.faces(
                "top",
                (0, -25, 4),
                (0, 25, 4),
                direction="vertical",
                offset_mm=10,
                decimals=0,
            ),
            DrawingDimension.radial(
                "top",
                (-25.171573, 2.828427, 8),
                diameter=True,
                override_text="2× {value} THRU",
                line_through_mm=(92, 88),
                decimals=0,
            ),
            DrawingDimension.radial(
                "top",
                (8.485281, 8.485281, 22),
                diameter=True,
                line_through_mm=(96, 69),
                decimals=0,
            ),
        ),
    )


sample_plate_drawing()
