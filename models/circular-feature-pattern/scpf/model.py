"""Native SolidCraft circular pattern over a direct Hole feature."""


class CircularFeaturePattern:
    bolts = 6
    pcd = 60.0

    def build(self):
        plate = Box(100, 100, 6, anchor=Anchor.BOTTOM)

        source_hole = Hole(
            d=8,
            direction=(0, 0, -1),
        ).at(self.pcd / 2, 0, 6)
        plate = plate + source_hole

        return plate.circular_pattern(
            source_hole,
            count=self.bolts,
            axis=Axis.Z,
        )


CircularFeaturePattern()
