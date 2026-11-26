"""Qualification: one size table plus an independent Installed rule."""


@component(include=("tube_d", "fit_diameter"))
class FlexibleSleeve:
    tube_d = 20.0
    fit_diameter = 20.4
    wall = 2.0
    HEIGHT = 20.0
    RELIEF_WIDTH = 2.0

    def build(self):
        outer = Cylinder(d=self.tube_d + 2 * self.wall, h=self.HEIGHT)
        bore = Cylinder(d=self.fit_diameter, h=self.HEIGHT + 2)
        relief = Box(12, self.RELIEF_WIDTH, self.HEIGHT + 2).move(x=6)
        return outer - bore - relief


class FlexibleFitState:
    frame_width = 80.0
    tube_d = 20.0
    fit_diameter = 20.4

    def build(self):
        left = FlexibleSleeve(
            tube_d=self.tube_d,
            fit_diameter=self.fit_diameter,
            name="left_sleeve",
            placement=Placement(x=-self.frame_width / 4),
        )
        right = left.copy(
            name="right_sleeve",
            placement=Placement(x=self.frame_width / 4),
        )

        return Configure(
            left + right,
            active="Medium",
            columns=(
                Param(self.frame_width),
                Param(self.fit_diameter),
            ),
            rows={
                "Small": ("60 mm", "20.4 mm"),
                "Medium": ("80 mm", "20.4 mm"),
                "Large": ("100 mm", "20.4 mm"),
            },
            rules=(
                ConfigRule(
                    "installed",
                    "Installed",
                    enabled=True,
                    condition=Always(),
                    effect=DriveParameter(self.fit_diameter, self.tube_d),
                ),
            ),
        )


FlexibleFitState()
