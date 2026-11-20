"""Qualification fixture for the four native Hole-family features."""


class HoleFamily:
    width = 120.0
    depth = 40.0
    thickness = 12.0

    def build(self):
        body = Box(
            self.width,
            self.depth,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )
        top = self.thickness

        body = body + Hole(
            d=6,
            direction=(0, 0, -1),
        ).at(-45, 0, top)

        body = body + CounterboreHole(
            d=6,
            counterbore_d=12,
            counterbore_depth=4,
            direction=(0, 0, -1),
        ).at(-15, 0, top)

        body = body + CountersinkHole(
            d=6,
            countersink_d=12,
            countersink_angle=90,
            direction=(0, 0, -1),
        ).at(15, 0, top)

        body = body + ThreadedHole(
            thread="M6",
            d=5,
            direction=(0, 0, -1),
            thread_depth=10,
            modeled=True,
            ease_out="short",
        ).at(45, 0, top)

        return body


HoleFamily()
