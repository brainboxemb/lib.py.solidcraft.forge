"""pyBOSL2 anchor reference for the parametric-anchor qualification."""

from pybosl2 import Anchor, cuboid

base = cuboid([40, 30, 10]).up(5)
block = cuboid([20, 20, 10]).up(5)
model = base.attach(Anchor.RIGHT, block, child_anchor=Anchor.LEFT).realize()
