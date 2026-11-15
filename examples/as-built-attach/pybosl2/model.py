"""pyBOSL2 geometry reference for an already positioned marker.

Both boxes use their bottom-face datum so the translated marker occupies
Z=15..23. Forge's as_built=True additionally records a native SolidCraft
relationship without re-solving this visible pose.
"""

from pybosl2 import Anchor, cuboid

base = cuboid([40, 30, 10], anchor=Anchor.BOTTOM)
marker = (
    cuboid([30, 10, 8], anchor=Anchor.BOTTOM)
    .rotate(90, [0, 0, 1])
    .translate([50, 20, 15])
)
model = base | marker
