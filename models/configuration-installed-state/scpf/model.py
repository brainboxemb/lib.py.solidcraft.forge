"""Qualification: one flexible-fit component has Free and Installed native states."""


class FlexibleFitState:
    fit_diameter = 20.4
    height = 20.0
    relief_width = 2.0

    def build(self):
        sleeve = Cylinder(d=self.fit_diameter, h=self.height)
        relief = Box(12, self.relief_width, 22).move(x=6)
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
