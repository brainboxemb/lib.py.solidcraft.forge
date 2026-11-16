"""Qualification fixture for all five native SolidCraft Slot creators."""


class SlotFamily:
    SLOT_WIDTH = 8.0

    def build(self):
        body = Box(160, 120, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Slot family", on=body) as slots:
            SlotCenterToCenter2D((-60, -35), (-40, -35), self.SLOT_WIDTH)
            SlotOverall2D((-10, -35), (20, -35), self.SLOT_WIDTH)
            SlotCenterPoint2D((55, -35), (65, -35), self.SLOT_WIDTH)
            SlotArcThreePoint2D((-50, 25), (-35, 38), (-20, 25), self.SLOT_WIDTH)
            SlotArcCenter2D((40, 25), (52, 25), self.SLOT_WIDTH, sweep=120)

        return body - slots.extrude(-5)


SlotFamily()
