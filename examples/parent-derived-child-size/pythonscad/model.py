"""PythonSCAD reference: child dimensions are half the parent dimensions."""

from pythonscad import *

base_width = 120.0
base_depth = 80.0

parent = cube([base_width, base_depth, 10], center=True).up(5)
child = cube([base_width / 2, base_depth / 2, 6], center=True).up(23)
show(parent | child)
