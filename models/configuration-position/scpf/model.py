"""Generic configuration-table qualification for parameter-driven assembly positions."""


class Screen:
    def build(self):
        return Box(80, 10, 50)


class FrontPlate:
    def build(self):
        return Box(80, 2, 50)


class ConfigurationPosition:
    plate_y = 8.0
    plate_z = 0.0

    def build(self):
        screen = Screen(name="screen")
        front_plate = FrontPlate(
            name="front_plate",
            placement=Placement(y=self.plate_y, z=self.plate_z),
        )
        return Configure(
            screen + front_plate,
            active="Front",
            columns=(Param(self.plate_y), Param(self.plate_z)),
            rows={
                "Front": ("8 mm", "0 mm"),
                "Below": ("0 mm", "-55 mm"),
                "Service": ("25 mm", "0 mm"),
            },
        )


ConfigurationPosition()
