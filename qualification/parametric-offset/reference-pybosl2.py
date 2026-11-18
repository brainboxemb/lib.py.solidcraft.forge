"""pyBOSL2 geometry reference for the parametric-offset case.

This keeps the visible placement explicit. Forge's qualification additionally
checks a persisted local joint-frame offset after native parameter mutation.
"""

from pybosl2 import cuboid

shift = 5.0
base = cuboid([40, 30, 20]).up(10)
marker = cuboid([10, 10, 10]).translate([15, -20, 20])
model = base | marker
