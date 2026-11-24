"""Qualification fixture for SolidCraft 0.45 native parametric Slots."""


class SlotFamily:
    width = 160.0
    depth = 120.0
    thickness = 5.0

    slot_width = 8.0
    straight_y = -35.0

    c2c_start_x = -60.0
    c2c_end_x = -40.0

    overall_start_x = -10.0
    overall_end_x = 20.0

    center_point_x = 55.0
    center_point_end_x = 65.0

    def build(self):
        body = Box(
            self.width,
            self.depth,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )

        with Sketch(name="Slot family", on=body) as slots:
            SlotCenterToCenter2D(
                (self.c2c_start_x, self.straight_y),
                (self.c2c_end_x, self.straight_y),
                self.slot_width,
            )
            SlotOverall2D(
                (self.overall_start_x, self.straight_y),
                (self.overall_end_x, self.straight_y),
                self.slot_width,
            )
            SlotCenterPoint2D(
                (self.center_point_x, self.straight_y),
                (self.center_point_end_x, self.straight_y),
                self.slot_width,
            )
            SlotArcThreePoint2D(
                (-50, 25),
                (-35, 38),
                (-20, 25),
                self.slot_width,
            )
            SlotArcCenter2D(
                (40, 25),
                (52, 25),
                self.slot_width,
                sweep=120,
            )

        return body - slots.extrude(Depth.THROUGH_ALL)


SlotFamily()
