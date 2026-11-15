"""PythonSCAD geometry reference for associative attachment seed placement."""

from pythonscad import *

left = cube([20, 20, 100], center=True).up(50)
right = cube([20, 20, 100], center=True).up(50).right(80)
left_marker = cube([10, 10, 10], center=True).up(105)
right_marker = cube([10, 10, 10], center=True).up(105).right(80)

model = left | right | left_marker | right_marker
