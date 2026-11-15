"""pyBOSL2 geometry reference for two normally translated blocks.

This reference matches the baseline geometry only. Forge separately qualifies
the native SolidCraft expressed occurrence placement.
"""

from pybosl2 import cuboid

fixed = cuboid([20, 20, 10]).up(5)
moved = cuboid([20, 20, 10]).up(5).right(40)
model = fixed | moved
