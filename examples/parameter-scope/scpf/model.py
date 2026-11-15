"""Parameter scope qualification: explicit component publication and inherited bindings."""


@component(include=("width",))
class Panel:
    width = 40.0
    depth = 20.0
    HEIGHT = 10.0
    _x = 0.0

    def build(self):
        # _x is fixed fixture layout, not a public occurrence-placement
        # dependency. Keeping it in the body preserves the existing visual
        # qualification while this case stays focused on parameter scope.
        return Box(self.width, self.depth, self.HEIGHT).move(\n            x=self._x,\n            z=self.HEIGHT / 2,\n        )


class ParameterScope:
    shared_width = 80.0

    def build(self):
        local = Panel(name="local", _x=0)
        override = Panel(width=60.0, name="override", _x=100)

        shared_a = Panel(width=self.shared_width, name="shared_a", _x=220)
        shared_b = shared_a.copy(
            name="shared_b",
            placement=Placement(x=120),
        )

        derived = Panel(
            width=half(self.shared_width),
            name="derived",
            _x=460,
        )

        return local + override + shared_a + shared_b + derived


ParameterScope()
