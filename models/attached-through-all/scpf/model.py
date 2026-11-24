"""Attached Polygon2D THROUGH_ALL cut regression model."""


class AttachedThroughAll:
    width = 80.0
    depth = 60.0
    thickness = 5.0

    def build(self):
        body = Box(
            self.width,
            self.depth,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )
        with Sketch(name="Through cut", on=body, parent=Anchor.TOP) as cut:
            Polygon2D([
                (-10, -8),
                (10, -8),
                (10, 8),
                (-10, 8),
            ])
        return body - cut.extrude(Depth.THROUGH_ALL)


AttachedThroughAll()
