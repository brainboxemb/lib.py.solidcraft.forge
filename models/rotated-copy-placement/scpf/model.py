"""Qualification: copied Placement keeps translation when rotation is present."""


class Panel:
    def build(self):
        return Box(20, 10, 4)


class RotatedCopyPlacement:
    def build(self):
        left = Panel(
            placement=Placement(
                x=-40,
                rotation=(Z, 90),
            )
        )
        right = left.copy(
            placement=Placement(
                x=40,
                rotation=(Z, 90),
            )
        )
        return left + right


RotatedCopyPlacement()
