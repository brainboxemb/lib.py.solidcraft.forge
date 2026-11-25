"""Native two-face XZ extrusion boundary selection qualification for #148."""


class TopologyFaceBoundaryXz:
    def build(self):
        with Sketch(name="Hook profile", plane="XZ") as sketch:
            Polygon2D(
                [(-20, 0), (20, 0), (20, 30), (-20, 30)],
                plane="XZ",
                world=True,
            )
        body = sketch.extrude(15, sym=True)
        return body.chamfer(
            1.5,
            edges=Edges.from_faces(Faces.FRONT, Faces.BACK),
        )


TopologyFaceBoundaryXz()
