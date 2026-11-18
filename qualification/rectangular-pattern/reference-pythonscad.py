"""PythonSCAD geometry reference for the 3 x 2 rectangular slot pattern."""

from pythonscad import *

plate = cube([120, 80, 4], center=True).up(2)

def slot_cut(x, y):
    bar = cube([10, 6, 8], center=True).translate([x, y, 2])
    left = cylinder(d=6, h=8, center=True).translate([x - 5, y, 2])
    right = cylinder(d=6, h=8, center=True).translate([x + 5, y, 2])
    return bar | left | right

cutters = None
for y in (0, 28):
    for x in (0, 24, 48):
        cutter = slot_cut(x, y)
        cutters = cutter if cutters is None else cutters | cutter

model = plate - cutters
