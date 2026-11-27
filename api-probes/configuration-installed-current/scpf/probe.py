"""Current native baseline for standalone Free/Installed configuration UI."""


@component(include=("tube_d", "clamp_bore"))
class FlexibleClamp:
    tube_d = 10.0
    clamp_bore = 9.6
    wall = 2.0
    height = 16.0

    def build(self):
        outer = Cylinder(d=self.tube_d + 2 * self.wall, h=self.height)
        bore = Cylinder(d=self.clamp_bore, h=self.height + 2)
        relief = Box(8, 1.5, self.height + 2).move(x=4)
        return outer - bore - relief


class ConfigurationInstalledCurrent:
    tube_d = 10.0
    clamp_interference = 0.4
    clamp_bore = 9.6

    def build(self):
        clamp = FlexibleClamp(
            tube_d=self.tube_d,
            clamp_bore=self.clamp_bore,
            name="clamp",
        )

        return Configure(
            clamp,
            active="Free",
            columns=(Param(self.clamp_bore),),
            rows={
                "Free": ("tube_d-clamp_interference",),
            },
            rules=(
                ConfigRule(
                    "installed",
                    "Installed",
                    enabled=False,
                    condition=Always(),
                    effect=DriveParameter(self.clamp_bore, self.tube_d),
                ),
            ),
        )


ConfigurationInstalledCurrent()
