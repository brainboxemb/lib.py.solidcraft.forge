"""pyBOSL2 reference: a plate with two symmetric through holes."""

from pybosl2 import cuboid, cyl

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cuboid([width, depth, thickness]).up(thickness / 2)
hole = cyl(diameter=8, height=thickness + 2).up(thickness / 2)
holes = hole.back(spacing / 2) | hole.front(spacing / 2)
(plate - holes).show()
