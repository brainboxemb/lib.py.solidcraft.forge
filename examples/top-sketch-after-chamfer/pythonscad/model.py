"""PythonSCAD geometry reference for a chamfered plate with one through hole."""

from pythonscad import *


CUTTER_SIZE = 100.0
CHAMFER_LINE = 50.0 + 35.0 - 8.0
CUTTER_CENTER = (
    CHAMFER_LINE / 2.0
    + CUTTER_SIZE / (2.0 * (2.0 ** 0.5))
)

plate = cube([100, 70, 10], center=True).translate([0, 0, 5])
for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    cutter = (
        cube([CUTTER_SIZE, CUTTER_SIZE, 20], center=True)
        .rotate([0, 0, 45])
        .translate([sx * CUTTER_CENTER, sy * CUTTER_CENTER, 5])
    )
    plate = plate - cutter

hole = cylinder(d=12, h=20).translate([0, 0, -5])
model = plate - hole
