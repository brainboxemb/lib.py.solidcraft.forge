"""pyBOSL2 reference: a plate with two symmetric through holes.

The qualification intent uses the lower-left-bottom world corner as (0, 0, 0).
pyBOSL2 primitives are centred by default, so this reference places their
centres explicitly while preserving the same visible geometry.
"""

from pybosl2 import cuboid, cyl

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cuboid([width, depth, thickness]).translate(
    [width / 2, depth / 2, thickness / 2]
)
hole = cyl(diameter=8, height=thickness + 2)
left_hole = hole.translate(
    [width / 2, depth / 2 - spacing / 2, thickness / 2]
)
right_hole = hole.translate(
    [width / 2, depth / 2 + spacing / 2, thickness / 2]
)
model = plate - (left_hole | right_hole)
