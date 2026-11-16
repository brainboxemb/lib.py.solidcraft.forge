"""pyBOSL2 reference for the SimpleBox qualification intent.

pyBOSL2 cuboid() is centered by default, but its native Anchor.BOTTOM places
the bottom-face centre at Z=0. That expresses the same origin intent as
Forge/SolidCraft Box directly; no corrective translation is needed.
"""

from pybosl2 import Anchor, cuboid

length = 40.0
width = 30.0
height = 10.0

model = cuboid([length, width, height], anchor=Anchor.BOTTOM)
