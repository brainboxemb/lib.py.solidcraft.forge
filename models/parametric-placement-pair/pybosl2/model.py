"""pyBOSL2 geometry reference for a symmetric pair of translated blocks."""

from pybosl2 import cuboid

left = cuboid([20, 20, 10]).left(40)
right = cuboid([20, 20, 10]).right(40)
model = left | right
