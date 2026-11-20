"""Native selective Sketch profile extrusion qualification.

One Circle seed creates four associative profiles. The extrusion cuts only
three of them by fixed sketch-local profile points.
"""


class SelectiveProfileExtrude:
    hole_diameter = 8.0
    hole_pitch = 20.0

    def build(self):
        board = Box(120, 60, 5, anchor=Anchor.BOTTOM)

        with Sketch(name="Selected holes", on=board, parent=Anchor.TOP) as holes:
            seed = holes.add(
                Circle2D(d=self.hole_diameter),
                offset=(-30, 0),
            )
            holes.rectangular_pattern(
                seed,
                count=4,
                spacing=self.hole_pitch,
                direction=Axis.X,
            )

        return board - holes.extrude(
            Depth.THROUGH_ALL,
            profiles=[(-30, 0), (-10, 0), (30, 0)],
            exact_regions=True,
        )


SelectiveProfileExtrude()
