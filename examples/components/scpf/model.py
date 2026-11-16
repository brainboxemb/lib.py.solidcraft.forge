class Block:
    length = 40.0
    width = 30.0
    height = 10.0

    def build(self):
        return Box(self.length, self.width, self.height, anchor=Anchor.BOTTOM)


class TwoBlocks:
    def build(self):
        left = Block()
        right = left.copy(
            placement=Placement(x=Block.length),
        )

        # left/right are ModelInstance occurrences here. Their + operator
        # creates an Assembly; it is not the Shape + Boolean/feature operator.
        return left + right


TwoBlocks()
