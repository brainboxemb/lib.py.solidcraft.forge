"""pyBOSL2 geometry reference for the XZ-board qualification intent."""

from pybosl2 import cuboid

board = cuboid([40, 12, 20]).translate([0, 6, 10])
right_marker = cuboid([10, 10, 10]).translate([15, -5, 15])
left_marker = cuboid([10, 10, 10]).translate([-15, -5, 15])
model = board | right_marker | left_marker
