"""Typed Forge placement IR qualification for an off-centre Cylinder cut."""


class CylinderSubtract:
    length = 60.0
    width = 40.0
    thickness = 12.0
    bore_d = 10.0
    bore_x = 8.0
    bore_y = -5.0

    def build(self):
        body = Box(
            self.length,
            self.width,
            self.thickness,
            anchor=Anchor.BOTTOM,
        )
        bore = Cylinder(
            d=self.bore_d,
            h=self.thickness + 20,
        ).at(
            self.bore_x,
            self.bore_y,
            0,
        )
        return body - bore


CylinderSubtract()
