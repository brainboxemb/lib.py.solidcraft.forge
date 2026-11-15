"""PythonSCAD geometry reference for a symmetric pair of translated blocks."""

from pythonscad import *

left = cube([20, 20, 10], center=True).up(5).left(40)
right = cube([20, 20, 10], center=True).up(5).right(40)
model = left | right
