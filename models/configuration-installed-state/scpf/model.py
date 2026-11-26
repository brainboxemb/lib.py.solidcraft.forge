"""Native proof: size rows and Installed are independent configuration axes."""


@component(include=("fit_diameter", "sleeve_height"))
class FlexibleSleeve:
    fit_diameter = 19.8
    sleeve_height = 30.0
    RELIEF_WIDTH = 2.0

    def build(self):
        sleeve = Cylinder(d=self.fit_diameter, h=self.sleeve_height)
        relief = Box(
            12,
            self.RELIEF_WIDTH,
            self.sleeve_height + 2,
        ).move(x=6)
        return sleeve - relief


class FlexibleFitState:
    tube_d = 20.0
    clamp_interference = 0.2
    fit_diameter = 19.8
    sleeve_height = 30.0

    def build(self):
        sleeve = FlexibleSleeve(
            fit_diameter=self.fit_diameter,
            sleeve_height=self.sleeve_height,
            name="flexible_sleeve",
        )
        free_fit = "tube_d - clamp_interference"
        return Configure(
            sleeve,
            active="Medium",
            columns=(
                Param(self.sleeve_height),
                Param(self.fit_diameter),
            ),
            rows={
                "Small": ("20 mm", free_fit),
                "Medium": ("30 mm", free_fit),
                "Large": ("40 mm", free_fit),
            },
        )


FlexibleFitState()
