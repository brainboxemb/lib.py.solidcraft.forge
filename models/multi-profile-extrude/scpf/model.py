"""Native multi-profile standalone Sketch extrusion qualification."""


class MultiProfileExtrude:
    outer_diameter = 10.0
    inner_diameter = 8.0
    length = 30.0

    def build(self):
        with Sketch(name="Tube profile", plane="XY") as profile:
            Circle2D(d=self.outer_diameter)
            Circle2D(d=self.inner_diameter)

        return profile.extrude(
            self.length,
            profiles=[(4.5, 0)],
            exact_regions=True,
        )


MultiProfileExtrude()
