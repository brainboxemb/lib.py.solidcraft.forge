"""Qualification: one size table plus an independent Installed rule."""


@component(include=("fit_diameter",))
class FlexibleSleeve:
    fit_diameter = 20.4
    HEIGHT = 20.0
    RELIEF_WIDTH = 2.0

    def build(self):
        sleeve = Cylinder(d=self.fit_diameter, h=self.HEIGHT)
        relief = Box(12, self.RELIEF_WIDTH, 22).move(x=6)
        return sleeve - relief


class FlexibleFitState:
    frame_width = 80.0
    fit_diameter = 20.4

    def build(self):
        left = FlexibleSleeve(
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
                    effect=DriveParameter(self.fit_diameter, 20.0),
                ),
            ),
        )


FlexibleFitState()
