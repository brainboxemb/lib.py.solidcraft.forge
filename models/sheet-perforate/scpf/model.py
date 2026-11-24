"""Public Verification model for SolidCraft whole-sheet perforations."""


class SheetPerforate:
    width = 60.0
    depth = 40.0
    thickness = 2.0
    bend_radius = 2.0
    k_factor = 0.5
    perforation_diameter = 5.0
    perforation_pitch = 10.0
    perforation_margin = 5.0

    def build(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(self.width, self.depth)

        sheet = blank.sheet_metal(
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="Perforation Rule",
        )
        return sheet.perforate(
            diameter=self.perforation_diameter,
            pitch=self.perforation_pitch,
            margin=self.perforation_margin,
            pattern="square",
        )


SheetPerforate()
