"""pyBOSL2 geometry reference for the assembly-owned-anchor case.

The visible geometry is comparable; Forge's named assembly datum and persisted
SolidCraft relationship are the qualification-specific behaviour.
"""

from pybosl2 import cuboid

base = cuboid([40, 30, 20]).up(10)
companion = cuboid([10, 10, 10]).translate([70, 0, 5])
marker = cuboid([10, 10, 10]).translate([15, -20, 15])
model = base | companion | marker
