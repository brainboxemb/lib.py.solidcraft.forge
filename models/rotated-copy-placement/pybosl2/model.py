"""pyBOSL2 geometry reference for two rotated rectangular panels."""

from pybosl2 import cuboid

left = cuboid([10, 20, 4]).left(40)
right = cuboid([10, 20, 4]).right(40)
model = left | right
