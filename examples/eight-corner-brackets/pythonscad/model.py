"""PythonSCAD reference: two short L profiles on each vertical frame corner."""

from pythonscad import *

frame = cube([120, 80, 60], center=True).up(30).fillet(8)

def l_profile():
    horizontal = cube([32, 4, 16], center=True).translate([12, -2, 8])
    vertical = cube([4, 32, 16], center=True).translate([-2, 12, 8])
    return horizontal | vertical

model = frame
for x, y, angle in [(-60, -40, 0), (60, -40, 90), (60, 40, 180), (-60, 40, 270)]:
    low = l_profile().rotz(angle).translate([x, y, 0])
    high = l_profile().rotz(angle).translate([x, y, 44])
    model = model | low | high

show(model)
