"""pyBOSL2 geometry reference for the PostPair subassembly."""

from pybosl2 import cuboid

post = cuboid([10, 10, 20]).up(10)
pair = post.left(15) | post.right(15)
model = pair
