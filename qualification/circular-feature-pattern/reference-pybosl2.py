"""pyBOSL2 reference for a six-hole circular feature pattern."""

from math import cos, pi, sin
from pybosl2 import cuboid, cyl


plate = cuboid([100, 100, 6]).up(3)
cutters = None

for index in range(6):
    angle = index * 2 * pi / 6
    x = 30 * cos(angle)
    y = 30 * sin(angle)
    hole = cyl(diameter=8, height=12).translate([x, y, 3])
    cutters = hole if cutters is None else cutters | hole

model = plate - cutters
