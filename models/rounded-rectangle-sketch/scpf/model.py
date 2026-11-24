"""Qualification: attached rounded pad plus standalone world-plane cut."""


class RoundedRectangleSketch:
    base_width = 80.0
    base_depth = 60.0
    base_height = 5.0
    pad_width = 40.0
    pad_depth = 30.0
    radius = 5.0
    pad_height = 8.0
    cut_width = 10.0
    cut_height = 2.0
    cut_y = 22.0
    cut_z = 2.5
    cut_length = 100.0

    def build(self):
        body = Box(
            self.base_width,
            self.base_depth,
            self.base_height,
            anchor=Anchor.BOTTOM,
        )

        with Sketch(name="Rounded pad", on=body) as pad:
            pad.add(
                RoundedRectangle2D(
                    self.pad_width,
                    self.pad_depth,
                    self.radius,
                ),
            )

        body = body + pad.extrude(self.pad_height)

        with Sketch(name="World cut", plane="YZ") as cut:
            cut.add(
                Rectangle2D(self.cut_width, self.cut_height),
                offset=(self.cut_y, self.cut_z),
            )

        return body - cut.extrude(self.cut_length, sym=True)


RoundedRectangleSketch()
