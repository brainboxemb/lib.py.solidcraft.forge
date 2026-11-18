"""Native sheet-metal fold fixture used by qualification #305."""


class SheetFold:
    width = 80.0
    depth = 40.0
    thickness = 2.0
    bend_radius = 2.0
    k_factor = 0.5
    fold_angle = 90.0
    hole_diameter = 6.0

    def build(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(self.width, self.depth)

        sheet = blank.sheet_metal(
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="SheetFold Rule",
        )

        sheet = sheet + Hole(
            d=self.hole_diameter,
            direction=(0, 0, -1),
        ).at(-20, 0, self.thickness)

        return sheet.fold(
            line=((20, -20), (20, 20)),
            angle=self.fold_angle,
            fixed=(-30, 0, 0),
        )


SheetFold()
