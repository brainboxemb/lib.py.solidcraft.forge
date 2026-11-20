"""Native associative Sketch pattern/mirror qualification.

One Circle seed and one Slot seed drive all repeated cut geometry. Pattern
counts and spacing stay as editable SolidCraft parameters.
"""


class SketchPatternMirror:
    hole_diameter = 8.0
    hole_columns = 4
    hole_pitch = 25.0
    slot_count = 2
    slot_pitch = 50.0

    SLOT_WIDTH = 8.0

    def build(self):
        board = Box(240, 160, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Dog holes", on=board, parent=Anchor.TOP) as holes:
            seed = holes.add(
                Circle2D(d=self.hole_diameter),
                offset=(-60, -45),
            )
            row = holes.rectangular_pattern(
                seed,
                count=self.hole_columns,
                spacing=self.hole_pitch,
                direction=Axis.X,
            )
            holes.mirror(row, axis=Axis.X)

        board = board - holes.extrude(Depth.THROUGH_ALL)

        with Sketch(name="Clamp slots", on=board, parent=Anchor.TOP) as slots:
            seed = SlotCenterToCenter2D((20, 20), (40, 20), self.SLOT_WIDTH)
            arm = slots.rectangular_pattern(
                seed,
                count=self.slot_count,
                spacing=self.slot_pitch,
                direction=Axis.X,
            )
            left = slots.mirror(arm, axis=Axis.Y)
            slots.mirror(arm, axis=Axis.X)
            slots.mirror(left, axis=Axis.X)

        return board - slots.extrude(Depth.THROUGH_ALL)


SketchPatternMirror()
