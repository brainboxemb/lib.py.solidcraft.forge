"""PythonSCAD geometry reference for a block placed on the base's right face."""

from pythonscad import *

base_width = 40.0
base = cube([base_width, 30, 10], center=True).up(5)
block = cube([20, 20, 10], center=True).up(5).right(base_width / 2 + 10)
model = base | block
