"""pyBOSL2 geometry reference for a marker touching a box corner.

Forge additionally qualifies the native corner relationship after parent
parameter changes; this file is the readable geometry comparison.
"""

from pybosl2 import cuboid

base = cuboid([40, 30, 20]).up(10)
marker = cuboid([10, 10, 10]).translate([15, -20, 15])
(base | marker).show()
