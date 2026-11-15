"""Qualification: RoundedRectangle2D in an explicit named Sketch."""


class RoundedRectangleSketch:
    base_width = 80.0
    base_depth = 60.0
    base_height = 5.0
    sketch_width = 40.0
    sketch_depth = 30.0
    radius = 5.0

    def build(self):
        body = Box(self.base_width, self.base_depth, self.base_height)

        with Sketch(name="Rounded rectangle", on=body) as sketch:
            sketch.add(
                RoundedRectangle2D(
                    self.sketch_width,
                    self.sketch_depth,
                    self.radius,
                ),
                offset=(-20, -15),
            )

        return body


RoundedRectangleSketch()
