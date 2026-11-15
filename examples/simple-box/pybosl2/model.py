"""pyBOSL2 reference for the SimpleBox qualification intent.

pyBOSL2 cuboid() is centered by default. Forge/SolidCraft Box starts from its
bottom face in Z. The up(height / 2) below only aligns those coordinate
conventions so the three reference models occupy the same world position.
"""

from pybosl2 import cuboid

length = 40.0
width = 30.0
height = 10.0

model = cuboid([length, width, height]).up(height / 2)
