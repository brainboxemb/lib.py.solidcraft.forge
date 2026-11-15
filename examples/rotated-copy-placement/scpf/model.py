"""Qualification: copied numeric translation and rotation stay one Placement."""


class Panel:
    def build(self):
        return Box(20, 10, 2)


class RotatedCopyPlacement:
    def build(self):
        first = Panel()
        second = first.copy(
            placement=Placement(
                x=30,
                z=40,
                rotation=(X, 90),
            )
        )
        return first + second


RotatedCopyPlacement()
