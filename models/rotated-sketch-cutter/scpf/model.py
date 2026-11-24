"""Rotated standalone Sketch cutter regression model."""


def wedge(name, origin, rotation):
    with Sketch(
        name=name,
        plane="XY",
        origin=origin,
        rotation=rotation,
    ) as sketch:
        Polygon2D([
            (-4, -4),
            (4, -4),
            (0, 4),
        ])
    return sketch.extrude(8)


class RotatedSketchCutter:
    def build(self):
        body = Box(60, 60, 30)
        left = wedge("Left wedge", (-12, 0, 0), (90, 0, 45))
        right = wedge("Right wedge", (12, 0, 0), (90, 0, -45))
        return body - left - right


RotatedSketchCutter()
