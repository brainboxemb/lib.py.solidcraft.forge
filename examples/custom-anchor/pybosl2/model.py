"""pyBOSL2 reference for a rotated arm with a marker at its tip.

The Forge parent frame is at the centre of the arm's +Y end face and the child
mount frame is at the marker's geometric centre (Z=5 in the marker's
bottom-based convention). pyBOSL2 position() places the child's local origin on
the parent anchor, so the child is raised by 5 mm first to make that local
origin coincide with its geometric centre. Forge additionally proves that the
named, oriented AnchorFrame survives on a rotated native occurrence.
"""

from pybosl2 import Anchor, cuboid

arm = cuboid([10, 40, 10]).up(5)
marker = cuboid([10, 10, 10]).up(5)
model = arm.position(Anchor.BACK, marker)
