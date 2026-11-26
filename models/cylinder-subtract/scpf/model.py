"""Typed Forge IR qualification for Cylinder subtract."""


class CylinderSubtract:
    length = 60.0
    width = 40.0
    thickness = 12.0
    bore_d = 10.0

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
        )
        return body - bore


CylinderSubtract()
