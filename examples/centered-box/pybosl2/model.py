"""pyBOSL2 reference for a box centered on its declared origin."""

from pybosl2 import Anchor, cuboid

length = 40.0
width = 30.0
height = 10.0

model = cuboid([length, width, height], anchor=Anchor.CENTER)
