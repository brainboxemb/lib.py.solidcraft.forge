"""pyBOSL2 geometry reference for an already positioned marker.

Forge's as_built=True additionally records a native SolidCraft relationship
without re-solving this pose; this reference preserves only the visible pose.
"""

from pybosl2 import cuboid

base = cuboid([40, 30, 10]).up(5)
marker = cuboid([30, 10, 8]).rotate(90, [0, 0, 1]).translate([50, 20, 15])
(base | marker).show()
