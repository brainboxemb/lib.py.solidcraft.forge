"""Qualification: native parametric occurrence placement without joints."""


class Block:
    def build(self):
        return Box(20, 20, 10)


class ParametricMove:
    offset = 40.0

    def build(self):
        fixed = Block()
        moved = Block().move(x=self.offset)
        return fixed + moved


ParametricMove()
