"""Native SolidCraft rectangular feature-pattern qualification."""


class RectangularPattern:
    columns = 3
    rows = 2
    pitch = 24.0
    row_pitch = 28.0

    def build(self):
        plate = Box(120, 80, 4, anchor=Anchor.BOTTOM)
        with Sketch(name="Slot", on=plate) as slot:
            SlotCenterToCenter2D((-5, 0), (5, 0), 6)

        source_cut = slot.extrude(-4)
        plate = plate - source_cut
        return plate.rectangular_pattern(
            source_cut,
            count=self.columns,
            spacing=self.pitch,
            direction=Axis.X,
            count2=self.rows,
            spacing2=self.row_pitch,
            direction2=Axis.Y,
        )


RectangularPattern()
