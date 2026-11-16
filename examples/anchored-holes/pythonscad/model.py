"""PythonSCAD reference: a 100 x 60 x 10 plate with two through holes.

This case deliberately uses the lower-left-bottom corner as world origin. The
PythonSCAD cube center code "---" places that datum on the minimum side of all
three axes, so the plate grows directly into +X/+Y/+Z without a corrective
translation.
"""

from pythonscad import *

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cube([width, depth, thickness], center="---")
hole = cylinder(d=8, h=thickness + 2, center=True)
left_hole = hole.translate([width / 2, depth / 2 - spacing / 2, thickness / 2])
right_hole = hole.translate([width / 2, depth / 2 + spacing / 2, thickness / 2])
model = plate - (left_hole | right_hole)
