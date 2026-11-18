"""pyBOSL2 reference: mate the arm to TOP and spin it 90 degrees."""

from pybosl2 import Anchor, cuboid

base = cuboid([60, 60, 10]).up(5)
arm = cuboid([30, 10, 6]).up(3)
model = base.attach(
    Anchor.TOP,
    arm,
    child_anchor=Anchor.BOTTOM,
    spin=90,
).realize()
