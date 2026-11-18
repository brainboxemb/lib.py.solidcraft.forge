"""pyBOSL2 geometry reference for a chamfered plate with one through hole."""

from pybosl2 import cuboid, cyl


CUTTER_SIZE = 100.0
CHAMFER_LINE = 50.0 + 35.0 - 8.0
CUTTER_CENTER = (
    CHAMFER_LINE / 2.0
    + CUTTER_SIZE / (2.0 * (2.0 ** 0.5))
)

plate = cuboid([100, 70, 10]).translate([0, 0, 5])
for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    cutter = (
        cuboid([CUTTER_SIZE, CUTTER_SIZE, 20])
        .rotate([0, 0, 45])
        .translate([sx * CUTTER_CENTER, sy * CUTTER_CENTER, 5])
    )
    plate = plate - cutter

hole = cyl(diameter=12, height=20).translate([0, 0, 5])
model = plate - hole
