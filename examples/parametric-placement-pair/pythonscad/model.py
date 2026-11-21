"""PythonSCAD geometry reference for a symmetric pair of translated blocks."""

from pythonscad import *

left = cube([20, 20, 10], center=True).left(40)
right = cube([20, 20, 10], center=True).right(40)
model = left | right
