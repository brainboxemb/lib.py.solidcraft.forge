"""Native qualification: TOP-attached Sketch on a circular extrusion."""


class RoundTopSketch:
    def build(self):
        with Sketch(name="Disc", plane="XY") as disc:
            Circle2D(d=100)
        body = disc.extrude(10)

        with Sketch(name="Hub", on=body, parent=Anchor.TOP) as hub:
            Circle2D(d=44)

        return body + hub.extrude(16)


RoundTopSketch()
