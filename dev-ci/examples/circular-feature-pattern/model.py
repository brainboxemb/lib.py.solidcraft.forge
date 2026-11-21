"""Native SolidCraft circular feature-pattern qualification."""


class CircularFeaturePattern:
    bolts = 6
    pcd = 60.0

    def build(self):
        plate = Box(100, 100, 6, anchor=Anchor.BOTTOM)

        with Sketch(name="BoltHole", on=plate, parent=Anchor.TOP) as bolt:
            bolt.add(
                Circle2D(d=8),
                offset=(self.pcd / 2, 0),
            )

        source_cut = bolt.extrude(Depth.THROUGH_ALL)
        plate = plate - source_cut

        return plate.circular_pattern(
            source_cut,
            count=self.bolts,
            axis=Axis.Z,
        )


CircularFeaturePattern()
