"""One shifted native revolve cut is one suppressible configuration feature."""


class ShiftedAxisRevolve:
    axis_x = 8.0
    axis_z = 3.0
    relief_d = 4.5
    core_d = 3.7

    def build(self):
        panel = Box(40, 24, 20)

        with Sketch(
            name="Stepped pass through",
            plane="XY",
            offset=self.axis_z,
        ) as profile:
            Polygon2D(
                [
                    (self.axis_x, -12),
                    (self.axis_x + self.relief_d / 2, -12),
                    (self.axis_x + self.relief_d / 2, -9),
                    (self.axis_x + self.core_d / 2, -9),
                    (self.axis_x + self.core_d / 2, 9),
                    (self.axis_x + self.relief_d / 2, 9),
                    (self.axis_x + self.relief_d / 2, 12),
                    (self.axis_x, 12),
                ],
                plane="XY",
            )

        pass_through = profile.revolve(
            axis=AxisLine(
                Axis.Y,
                origin=(self.axis_x, 0, self.axis_z),
            ),
        )
        body = panel - pass_through

        return Configure(
            body,
            active="Cut",
            columns=(Suppress(pass_through),),
            rows={
                "Cut": (False,),
                "Suppressed": (True,),
            },
        )


ShiftedAxisRevolve()
