"""pyBOSL2 reference for an arm with a marker at its +X tip.

The Forge parent frame is at the centre of the arm's +X end face and the child
mount frame is at the marker's geometric centre. pyBOSL2 position() expresses
the same visible attachment through its native anchor model. realize() is
required so the independently exported STL contains both solids.
"""

from pybosl2 import Anchor, cuboid

arm = cuboid([40, 10, 10]).up(5)
marker = cuboid([10, 10, 10])
model = arm.position(Anchor.RIGHT, marker).realize()
