"""pyBOSL2 reference for a rotated arm with a marker at its tip.

The Forge parent frame is at the centre of the arm's +Y end face and the child
mount frame is at the marker's geometric centre. pyBOSL2 position() expresses
that visible placement directly. Forge additionally proves that the named,
oriented AnchorFrame survives on a rotated native occurrence.
"""

from pybosl2 import Anchor, cuboid

arm = cuboid([10, 40, 10]).up(5)
marker = cuboid([10, 10, 10])
model = arm.position(Anchor.BACK, marker)
