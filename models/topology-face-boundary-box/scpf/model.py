"""Native one-face boundary selection qualification for #148."""


class TopologyFaceBoundaryBox:
    def build(self):
        body = Box(60, 40, 12, anchor=Anchor.BOTTOM)
        return body.chamfer(
            2,
            edges=Edges.from_faces(Faces.TOP),
        )


TopologyFaceBoundaryBox()
