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
            # Keep this qualification's original lower-left datum. Rectangle2D
            # is centered by default now, so the Forge fixture states the old
            # placement explicitly instead of moving the reference models.
            sketch.add(
                profile,
                offset=(self.width / 2, self.depth / 2),
            )
        plate = sketch.extrude(self.thickness)
        holes = Hole(d=8, depth=Depth.THROUGH_ALL).pattern(
            count=2, spacing=self.spacing, axis=Axis.Y
        ).on(plate, face=Faces.TOP)
        plate + holes


AnchoredHoles()
