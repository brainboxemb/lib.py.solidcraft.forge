"""Native regression fixture for SolidCraft edge-flange history."""


class SheetEdgeFlange:
    width = 80.0
    depth = 40.0
    thickness = 2.0
    bend_radius = 2.0
    k_factor = 0.5
    flange_height = 20.0
    flange_angle = 90.0

    def build(self):
        with Sketch(name="Blank", plane="XY") as blank:
            Rectangle2D(self.width, self.depth)

        sheet = blank.sheet_metal(
            thickness=self.thickness,
            bend_radius=self.bend_radius,
            k_factor=self.k_factor,
            rule_name="Edge Flange Rule",
        )
        return sheet.flange(
            edges=[(40, 0, 2)],
            height=self.flange_height,
            angle=self.flange_angle,
        )


SheetEdgeFlange()
