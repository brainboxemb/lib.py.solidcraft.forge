"""pyBOSL2 geometry reference for the group-hierarchy qualification.

This compares geometry only; Forge additionally qualifies native SolidCraft
component hierarchy/BOM structure.
"""

from pybosl2 import cuboid

panel = cuboid([10, 2, 20]).up(10)
panels = panel | panel.right(11)
frame = cuboid([35, 10, 40]).up(20).back(20)
model = panels | frame
