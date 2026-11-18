"""pyBOSL2 geometry reference for selective profile extrusion."""

from pybosl2 import cuboid, cyl

plate = cuboid([120, 60, 5]).translate([0, 0, 2.5])
cutters = None
for x in (-30, -10, 30):
    hole = cyl(diameter=8, height=7).translate([x, 0, 2.5])
    cutters = hole if cutters is None else cutters | hole

model = plate - cutters
