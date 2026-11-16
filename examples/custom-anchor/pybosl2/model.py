"""pyBOSL2 reference for a rotated arm with a marker at its tip.

The Forge parent frame is at the centre of the arm's +Y end face and the child
mount frame is at the marker's geometric centre. pyBOSL2 position() places the
child's local origin on the parent anchor, so a centred marker expresses the
same visible placement directly. position() stores the child as a deferred
attachment; realize() is required here so the independently exported STL
contains both solids.

Forge additionally proves that the named, oriented AnchorFrame survives on a
rotated native occurrence.
"""

from pybosl2 import Anchor, cuboid

arm = cuboid([10, 40, 10]).up(5)
marker = cuboid([10, 10, 10])
model = arm.position(Anchor.BACK, marker).realize()
