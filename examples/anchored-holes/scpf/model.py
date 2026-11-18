"""Face-relative Hole cut repeated by one native history pattern."""

from dataclasses import dataclass


@dataclass
class AnchoredHoles:
    """Two through holes, each 20 mm from the center along the Y axis."""

    width: float = 100
    depth: float = 60
    thickness: float = 10
    spacing: float = 40

    def build(self):
        with Sketch(name="Base", plane="XY") as sketch:
            profile = Rectangle2D(self.width, self.depth)
            sketch.add(
                profile,
                offset=(self.width / 2, self.depth / 2),
            )

        plate = sketch.extrude(self.thickness)

        with Sketch(
            name="Hole",
            on=plate,
            parent=Anchor.TOP,
        ) as hole:
            hole.add(
                Circle2D(d=8),
                offset=(0, -(self.spacing / 2)),
            )

        source_cut = hole.extrude(Depth.THROUGH_ALL)
        plate = plate - source_cut

        return plate.rectangular_pattern(
            source_cut,
            count=2,
            spacing=self.spacing,
            direction=Axis.Y,
        )


AnchoredHoles()
