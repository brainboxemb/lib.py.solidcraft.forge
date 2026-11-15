"""pyBOSL2 geometry reference for a rotated arm with a tip marker.

pyBOSL2 supplies anchor placement, while the Forge fixture specifically proves
a named oriented AnchorFrame carried by a rotated native occurrence.
"""

from pybosl2 import Anchor, cuboid

arm = cuboid([10, 40, 10]).up(5)
marker = cuboid([10, 10, 10]).up(5)
model = arm.attach(Anchor.BACK, marker, child_anchor=Anchor.FRONT).realize()
