"""PythonSCAD geometry reference for two rotated rectangular panels."""

from pythonscad import *

left = cube([10, 20, 4], center=True).left(40)
right = cube([10, 20, 4], center=True).right(40)
model = left | right
