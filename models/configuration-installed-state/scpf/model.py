"""Qualification: one flexible-fit component has Free and Installed native states."""


class FlexibleFitState:
    fit_diameter = 20.4
    HEIGHT = 20.0
    RELIEF_WIDTH = 2.0

    def build(self):
        sleeve = Cylinder(d=self.fit_diameter, h=self.HEIGHT)
        relief = Box(12, self.RELIEF_WIDTH, 22).move(x=6)
        part = sleeve - relief

        return Configure(
            part,
            active="Free",
            columns=(Param(self.fit_diameter),),
            rows={
                "Free": ("20.4 mm",),
                "Installed": ("20.0 mm",),
            },
        )


FlexibleFitState()
