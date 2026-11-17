"""Minimal reproduction for attached Sketch THROUGH_ALL cut direction."""


class AttachedThroughAll:
    width = 80.0
    depth = 60.0
    thickness = 5.0
    hole_diameter = 10.0

    def build(self):
        body = Box(
            self.width,
            self.depth,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )
        with Sketch(name="Through cut", on=body) as cut:
            Circle2D(d=self.hole_diameter)
        return body - cut.extrude(Depth.THROUGH_ALL)


AttachedThroughAll()
