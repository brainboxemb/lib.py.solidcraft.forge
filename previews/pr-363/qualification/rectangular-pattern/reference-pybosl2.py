"""pyBOSL2 geometry reference for the 3 x 2 rectangular slot pattern."""

from pybosl2 import cuboid, cyl

plate = cuboid([120, 80, 4]).up(2)

def slot_cut(x, y):
    bar = cuboid([10, 6, 8]).translate([x, y, 2])
    left = cyl(diameter=6, height=8).translate([x - 5, y, 2])
    right = cyl(diameter=6, height=8).translate([x + 5, y, 2])
    return bar | left | right

cutters = None
for y in (0, 28):
    for x in (0, 24, 48):
        cutter = slot_cut(x, y)
        cutters = cutter if cutters is None else cutters | cutter

model = plate - cutters
