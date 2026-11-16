class Block:
    length = 40.0
    width = 30.0
    height = 10.0

    def build(self):
        return Box(self.length, self.width, self.height, anchor=BOTTOM)


class TwoBlocks:
    def build(self):
        left = Block()
        right = left.copy(
            placement=Placement(x=Block.length),
        )

        return left + right


TwoBlocks()
