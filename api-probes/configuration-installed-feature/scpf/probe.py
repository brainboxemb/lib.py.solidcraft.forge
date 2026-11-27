"""Probe Installed as a real suppressible component feature.

Free keeps the Installed cutter suppressed, leaving a 9.6 mm bore.
Installed unsuppresses the same feature, widening the bore to 10.0 mm.
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

        installed = (
            Cylinder(d=self.tube_d, h=self.height + 2)
            .export_feature("installed")
        )

        return outer - free_bore - relief - installed


class ConfigurationInstalledFeature:
    tube_d = 10.0
    free_bore = 9.6

    def build(self):
        clamp = FlexibleClamp(
            tube_d=self.tube_d,
            free_bore=self.free_bore,
            name="clamp",
        )

        return Configure(
            clamp,
            active="Free",
            columns=(
                Suppress(clamp.feature("installed")),
            ),
            rows={
                "Free": (True,),
                "Installed": (False,),
            },
        )


ConfigurationInstalledFeature()
