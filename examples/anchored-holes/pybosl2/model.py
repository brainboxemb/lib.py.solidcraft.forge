"""pyBOSL2 reference: a centred plate with two symmetric through holes."""

from pybosl2 import cuboid, cyl

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cuboid([width, depth, thickness]).up(thickness / 2)
hole = cyl(diameter=8, height=thickness + 2)
left_hole = hole.translate([0, -spacing / 2, thickness / 2])
right_hole = hole.translate([0, spacing / 2, thickness / 2])
model = plate - (left_hole | right_hole)
