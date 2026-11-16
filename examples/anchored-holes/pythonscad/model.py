"""PythonSCAD reference: a centred 100 x 60 x 10 plate with two holes."""

from pythonscad import *

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cube([width, depth, thickness], center=True).up(thickness / 2)
hole = cylinder(d=8, h=thickness + 2, center=True)
left_hole = hole.translate([0, -spacing / 2, thickness / 2])
right_hole = hole.translate([0, spacing / 2, thickness / 2])
model = plate - (left_hole | right_hole)
