"""Qualification fixture for all five native SolidCraft Slot creators."""


class SlotFamily:
    width = 160.0
    depth = 120.0
    thickness = 5.0

    slot_width = 8.0

    def build(self):
        body = Box(
            self.width,
            self.depth,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )

        with Sketch(name="Slot family", on=body) as slots:
            SlotCenterToCenter2D((-60, -35), (-40, -35), self.slot_width)
            SlotOverall2D((-10, -35), (20, -35), self.slot_width)
            SlotCenterPoint2D((55, -35), (65, -35), self.slot_width)
            SlotArcThreePoint2D((-50, 25), (-35, 38), (-20, 25), self.slot_width)
            SlotArcCenter2D((40, 25), (52, 25), self.slot_width, sweep=120)

        return body - slots.extrude(Depth.THROUGH_ALL)


SlotFamily()
