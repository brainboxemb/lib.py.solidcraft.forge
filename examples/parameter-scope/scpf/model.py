"""Parameter scope qualification: explicit component publication and inherited bindings."""

from scpf import component


@component(include=("width",))
class Panel:
    width = 40.0
    depth = 20.0
    HEIGHT = 10.0

    def build(self):
        return Box(self.width, self.depth, self.HEIGHT)


class ParameterScope:
    shared_width = 80.0

    def build(self):
        local = Panel(name="local", placement=Placement(x=0))
        override = Panel(width=60.0, name="override", placement=Placement(x=100))

        shared_a = Panel(width=self.shared_width, name="shared_a", placement=Placement(x=220))
        shared_b = Panel(width=self.shared_width, name="shared_b", placement=Placement(x=340))

        derived = Panel(
            width=half(self.shared_width),
            name="derived",
            placement=Placement(x=460),
        )

        return local + override + shared_a + shared_b + derived


ParameterScope()
