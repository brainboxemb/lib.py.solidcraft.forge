"""PythonSCAD geometry reference for the front/top/right corner marker."""

from pythonscad import *

base = cube([40, 30, 20], center=True).up(10)
marker = cube([10, 10, 10], center=True).translate([15, -20, 15])
model = base | marker
