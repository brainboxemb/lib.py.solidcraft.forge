"""PythonSCAD geometry reference for a right-side attachment with a 10 mm gap."""

from pythonscad import *

gap = 10.0
base = cube([40, 30, 10], center=True).up(5)
block = cube([20, 20, 10], center=True).up(5).right(30 + gap)
model = base | block
