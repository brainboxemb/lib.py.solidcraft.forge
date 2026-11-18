"""PythonSCAD geometry reference for selective profile extrusion."""

from pythonscad import *

CUT_HEIGHT = 9
CUT_Z = -2

plate = cube([120, 60, 5], center=True).up(2.5)
cutters = None
for x in (-30, -10, 30):
    hole = cylinder(d=8, h=CUT_HEIGHT).translate([x, 0, CUT_Z])
    cutters = hole if cutters is None else cutters | hole

model = plate - cutters
