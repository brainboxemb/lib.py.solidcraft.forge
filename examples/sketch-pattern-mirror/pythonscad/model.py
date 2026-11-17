"""PythonSCAD geometry reference for sketch pattern/mirror qualification."""

from pythonscad import *

CUT_HEIGHT = 9
CUT_Z = -2


def straight_slot(cx, cy, center_separation=20, width=8):
    bar = cube([center_separation, width, CUT_HEIGHT], center=True).translate(
        [cx, cy, 2.5]
    )
    left = cylinder(d=width, h=CUT_HEIGHT).translate(
        [cx - center_separation / 2, cy, CUT_Z]
    )
    right = cylinder(d=width, h=CUT_HEIGHT).translate(
        [cx + center_separation / 2, cy, CUT_Z]
    )
    return bar | left | right


plate = cube([240, 160, 5], center=True).up(2.5)
cutters = None

for y in (-45, 45):
    for x in (-60, -35, -10, 15):
        hole = cylinder(d=8, h=CUT_HEIGHT).translate([x, y, CUT_Z])
        cutters = hole if cutters is None else cutters | hole

for y in (-20, 20):
    for x in (-80, -30, 30, 80):
        slot = straight_slot(x, y)
        cutters = slot if cutters is None else cutters | slot

model = plate - cutters
