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
    """Final design presentation with Forge's default native ISO A4 drawing."""
    return SamplePlate().with_drawing(name="Sample Plate Drawing")


sample_plate_drawing()
