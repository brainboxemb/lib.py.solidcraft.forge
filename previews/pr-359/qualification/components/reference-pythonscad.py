"""PythonSCAD geometry reference for two side-by-side reusable blocks."""

from pythonscad import *

left = cube([40, 30, 10], center=True).up(5)
right = cube([40, 30, 10], center=True).up(5).right(40)
model = left | right
