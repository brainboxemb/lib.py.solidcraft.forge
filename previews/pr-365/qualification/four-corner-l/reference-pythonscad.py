"""PythonSCAD reference: four short L profiles centred on the frame corners."""

from pythonscad import *

frame = cube([120, 80, 60], center=True).up(30).fillet(8)

def l_profile():
    horizontal = cube([32, 4, 16], center=True).translate([12, -2, 0])
    vertical = cube([4, 32, 16], center=True).translate([-2, 12, 0])
    return horizontal | vertical

profile = l_profile()
model = frame
for x, y, angle in [(-60, -40, 0), (60, -40, 90), (60, 40, 180), (-60, 40, 270)]:
    model = model | profile.rotz(angle).translate([x, y, 30])
