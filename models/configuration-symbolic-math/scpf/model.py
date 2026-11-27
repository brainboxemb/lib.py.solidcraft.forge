"""Configuration-driven native symbolic CAD math qualification."""


class ConfigurationSymbolicMath:
    size = 70.0
    limit = 80.0
    offset = 20.0
    grid = 7.5
    pitch = 12.0
    step = 1.0
    wall = 4.0
    bias = -3.0

    def build(self):
        span = cadmath.sqrt(
            cadmath.min(self.size, self.limit) ** 2
            - self.offset ** 2
        )
        grid_span = cadmath.round(self.size / self.grid) * self.grid
        height = (
            cadmath.floor(self.size / self.pitch) * self.step
            + cadmath.max(self.wall, cadmath.abs(self.bias))
        )
        model = Box(
            span,
            grid_span,
            height,
            anchor=Anchor.BOTTOM,
        )
        model.configure(
            active="Medium",
            columns=(self.size,),
            rows={
                "Small": ("60 mm",),
                "Medium": ("70 mm",),
                "Large": ("100 mm",),
            },
        )
        return model


ConfigurationSymbolicMath()
