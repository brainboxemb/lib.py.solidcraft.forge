"""Native SolidCraft exploded-view qualification."""


class ExplodeBlock:
    length = 30.0
    width = 20.0
    height = 10.0

    def build(self):
        return Box(
            self.length,
            self.width,
            self.height,
            anchor=Anchor.BOTTOM,
        )


class ExplodedViews:
    def build(self):
        first = ExplodeBlock()
        second = first.copy(placement=Placement(x=40))
        third = first.copy(placement=Placement(x=80))

        assembly = first + second + third
        assembly = assembly.with_exploded_view(
            "Automatic",
            scale=1.25,
        )
        assembly = assembly.with_exploded_view(
            "Instructions",
            moves=[
                (second, (0, 25, 0)),
                (third, (0, 50, 10)),
            ],
        )
        return assembly.show_assembled()


ExplodedViews()
