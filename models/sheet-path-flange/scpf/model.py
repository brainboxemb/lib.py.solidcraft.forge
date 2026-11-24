"""Native regression fixture for SolidCraft sheet.path_flange history."""


class SheetPathFlange:
    width = 80.0
    depth = 40.0
    thickness = 2.0
    bend_radius = 2.0
    k_factor = 0.5
    path_height = 14.0
    path_radius = 3.0

    def build(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(self.width, self.depth)

        sheet = blank.sheet_metal(
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="Path Flange Rule",
        )

        with Sketch(name="Path", plane="XZ") as sketch:
            chain = sketch.chain(start=(40, 2))
            chain.line_to((40, self.path_height))
            path = chain.finish()

        return sheet.path_flange(
            edge=(40, 0, 2),
            path=path,
            radius=self.path_radius,
        )


SheetPathFlange()
