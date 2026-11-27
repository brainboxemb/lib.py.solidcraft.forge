"""Backend probe for a named suppressible component feature.

This deliberately uses simple bore-widening geometry to isolate native feature
suppression. It is backend evidence, not the consumer proof for a flexible clamp.
"""


@component(include=("tube_d", "free_bore"))
class FlexibleClamp:
    tube_d = 10.0
    free_bore = 9.6
    wall = 2.0
    height = 16.0

    def build(self):
        outer = Cylinder(d=self.tube_d + 2 * self.wall, h=self.height)
        free_bore = Cylinder(d=self.free_bore, h=self.height + 2)
        relief = Box(8, 1.5, self.height + 2).move(x=4)

        body = outer - free_bore - relief
        with feature("installed", suppressed=True):
            body = body - Cylinder(d=self.tube_d, h=self.height + 2)
        return body


class ConfigurationInstalledFeature:
    tube_d = 10.0
    free_bore = 9.6

    def build(self):
        clamp = FlexibleClamp(
            tube_d=self.tube_d,
            free_bore=self.free_bore,
            name="clamp",
        )
        clamp.configure(
            active="Free",
            columns=(clamp.feature("installed"),),
            rows={
                "Free": (True,),
                "Installed": (False,),
            },
        )
        return clamp


ConfigurationInstalledFeature()
