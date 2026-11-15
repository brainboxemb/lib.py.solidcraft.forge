"""PythonSCAD geometry reference for the history-policy fixture.

PythonSCAD builds the same visible boss/pad geometry. Forge separately
qualifies which SolidCraft history representation is retained for each boss.
"""

from pythonscad import *

body = cube([50, 50, 6], center=True).up(3)

def boss(x, y):
    outer = cylinder(d=12, h=10).translate([x, y, 6])
    bore = cylinder(d=4, h=12).translate([x, y, 5])
    return outer - bore

model = body | boss(-10, 0) | boss(0, 15) | boss(10, 0)
pad = cylinder(d=10, h=6).translate([0, -15, 6])
model = model | pad
