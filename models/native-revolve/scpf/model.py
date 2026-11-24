"""Native profile-driven revolve qualification."""


class NativeRevolve:
    length = 10.0
    radius = 4.0
    sweep = 360.0

    def build(self):
        with Sketch(name="RadialProfile", plane="XZ") as sketch:
            Polygon2D(
                [(0, 0), (0, self.radius),
                 (self.length, self.radius), (self.length, 0)],
                plane="XZ",
            )
        return sketch.revolve(axis=Axis.X, angle=self.sweep)


NativeRevolve()
