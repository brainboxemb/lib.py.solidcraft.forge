"""pyBOSL2 reference using face anchors instead of copied X coordinates."""

from pybosl2 import Anchor, cuboid

left = cuboid([40, 30, 10]).up(5)
right = cuboid([40, 30, 10]).up(5)
model = left.attach(Anchor.RIGHT, right, child_anchor=Anchor.LEFT).realize()
model.show()
