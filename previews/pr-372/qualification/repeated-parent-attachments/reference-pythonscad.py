"""PythonSCAD geometry reference for two parent/marker pairs."""

from pythonscad import *

parent_height = 40.0
left_parent = cube([20, 20, parent_height], center=True).up(parent_height / 2)
right_parent = left_parent.right(60)
left_marker = cube([10, 10, 10], center=True).up(parent_height + 5)
right_marker = left_marker.right(60)
model = left_parent | right_parent | left_marker | right_marker
