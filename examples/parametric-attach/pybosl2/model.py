"""pyBOSL2 anchor reference for a right-side attachment with a gap.

pyBOSL2 calls the signed face separation overlap; a negative overlap is a gap.
Forge additionally qualifies saved SolidCraft parameter mutation of this value.
"""

from pybosl2 import Anchor, cuboid

gap = 10.0
base = cuboid([40, 30, 10]).up(5)
block = cuboid([20, 20, 10]).up(5)
model = base.attach(
    Anchor.RIGHT,
    block,
    child_anchor=Anchor.LEFT,
    overlap=-gap,
).realize()
model.show()
