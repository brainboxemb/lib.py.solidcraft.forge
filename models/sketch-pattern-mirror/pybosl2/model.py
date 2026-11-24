"""pyBOSL2 geometry reference for sketch pattern/mirror qualification."""

from pybosl2 import cuboid, cyl

CUT_HEIGHT = 9


def straight_slot(cx, cy, center_separation=20, width=8):
    bar = cuboid([center_separation, width, CUT_HEIGHT]).translate([cx, cy, 2.5])
    left = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [cx - center_separation / 2, cy, 2.5]
    )
    right = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [cx + center_separation / 2, cy, 2.5]
    )
    return bar | left | right


plate = cuboid([240, 160, 5]).up(2.5)
cutters = None

for y in (-45, 45):
    for x in (-60, -35, -10, 15):
        hole = cyl(diameter=8, height=CUT_HEIGHT).translate([x, y, 2.5])
        cutters = hole if cutters is None else cutters | hole

for y in (-20, 20):
    for x in (-80, -30, 30, 80):
        slot = straight_slot(x, y)
        cutters = slot if cutters is None else cutters | slot

model = plate - cutters
