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

        # Drawing intent belongs to the finished design, not Block's reusable
        # definition. SolidCraft creates the sheet and standard views natively.
        return (left + right).with_drawing(
            left,
            name="Block drawing",
        )


TwoBlocks()
