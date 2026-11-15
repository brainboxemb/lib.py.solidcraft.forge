"""PythonSCAD reference: a 100 x 60 x 10 plate with two through holes."""

from pythonscad import *

width = 100
depth = 60
thickness = 10
spacing = 40

plate = cube([width, depth, thickness], center=True).up(thickness / 2)
hole = cylinder(d=8, h=thickness + 2, center=True).up(thickness / 2)
holes = hole.back(spacing / 2) | hole.front(spacing / 2)
show(plate - holes)
