"""Qualification: reusable flexible-fit component has Free and Installed states."""


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
    fit_diameter = 20.4

    def build(self):
        sleeve = FlexibleSleeve(
            fit_diameter=self.fit_diameter,
            name="flexible_sleeve",
        )
        return Configure(
            sleeve,
            active="Free",
            columns=(Param(self.fit_diameter),),
            rows={
                "Free": ("20.4 mm",),
                "Installed": ("20.0 mm",),
            },
        )


FlexibleFitState()
