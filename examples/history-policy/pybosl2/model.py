"""pyBOSL2 geometry reference for the history-policy fixture.

The visible geometry is comparable; native-vs-sketch feature history is a
SolidCraft/Forge qualification concern rather than a pyBOSL2 contract.
"""

from pybosl2 import cuboid, cyl

body = cuboid([50, 50, 6]).up(3)

def boss(x, y):
    outer = cyl(diameter=12, height=10).translate([x, y, 11])
    bore = cyl(diameter=4, height=12).translate([x, y, 11])
    return outer - bore

model = body | boss(-10, 0) | boss(0, 15) | boss(10, 0)
pad = cyl(diameter=10, height=6).translate([0, -15, 9])
model = model | pad
