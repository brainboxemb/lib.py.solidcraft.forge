"""Native regression fixture for SolidCraft sheet-hem history."""


class SheetHem:
    width = 80.0
    depth = 40.0
    thickness = 2.0
    bend_radius = 2.0
    k_factor = 0.5
    hem_length = 12.0
    hem_gap = 4.0

    def build(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(self.width, self.depth)

        sheet = blank.sheet_metal(
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="Hem Rule",
        )
        return sheet.hem(
            edges=[(40, 0, 2)],
            length=self.hem_length,
            gap=self.hem_gap,
        )


SheetHem()
