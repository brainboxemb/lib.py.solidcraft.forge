"""TOP-attached Sketch after a native chamfer.

The chamfer intentionally precedes the attached Sketch. This exercises replay
selection of the resulting planar +Z face through model.faces.
"""


class TopSketchAfterChamfer:
    def build(self):
        plate = Box(100, 70, 10, anchor=Anchor.BOTTOM)
        plate = plate.chamfer(8, edges=Edges.VERTICAL)

        with Sketch(
            name="Top hole",
            on=plate,
            parent=Anchor.TOP,
        ) as hole:
            Circle2D(d=12)

        return plate - hole.extrude(Depth.THROUGH_ALL)


TopSketchAfterChamfer()
