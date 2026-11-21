"""Qualification: symmetric parametric occurrence Placement without joints."""


class Block:
    def build(self):
        return Box(20, 20, 10)


class ParametricPlacementPair:
    spacing = 80.0

    def build(self):
        left = Block(
            placement=Placement(x=-half(self.spacing))
        )
        right = left.copy(
            placement=Placement(x=half(self.spacing))
        )
        return left + right


ParametricPlacementPair()
