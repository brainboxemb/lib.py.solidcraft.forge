"""Native regression fixture for SolidCraft contour-flange history."""


class SheetContourFlange:
    end_height = 30.0
    contour_width = 50.0
    thickness = 2.5
    bend_radius = 2.5
    k_factor = 0.44

    def build(self):
        with Sketch(name="Contour", plane="XZ") as sketch:
            chain = sketch.chain(start=(0, 0))
            chain.line_to((35, 0))
            chain.tangent_arc_to((40, 5))
            chain.line_to((40, self.end_height))
            contour = chain.finish()

        return contour.contour_flange(
            distance=self.contour_width,
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="Contour Flange Rule",
        )


SheetContourFlange()
