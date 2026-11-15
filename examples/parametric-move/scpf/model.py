"""Qualification: native parametric occurrence Placement without joints."""


class Block:
    def build(self):
        return Box(20, 20, 10)


class ParametricMove:
    offset = 40.0

    def build(self):
        fixed = Block()
        placed = Block().at(Position(x=self.offset))
        return fixed + placed


ParametricMove()
