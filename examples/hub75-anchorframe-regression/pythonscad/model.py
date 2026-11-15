"""PythonSCAD reference for the HUB75-like two-sideboard bracket layout."""

from pythonscad import *


left_board = cube([12, 60, 80], center=True).translate([-66, 30, 52])
right_board = cube([12, 60, 80], center=True).translate([66, 30, 52])


def l_profile():
    horizontal = cube([28, 24, 12], center=True).translate([14, 0, 6])
    vertical = cube([12, 24, 28], center=True).translate([-6, 0, -14])
    return horizontal | vertical


model = left_board | right_board
for x, angle in [(-72, 0), (72, 90)]:
    for y in (12, 48):
        model = model | l_profile().rotate([0, angle, 0]).translate([x, y, 104])

for x, angle in [(72, 180), (-72, 270)]:
    for y in (12, 48):
        model = model | l_profile().rotate([0, angle, 0]).translate([x, y, 0])
