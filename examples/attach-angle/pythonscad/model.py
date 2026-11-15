"""PythonSCAD geometry reference for a 90 degree clocked top attachment."""

from pythonscad import *

base = cube([60, 60, 10], center=True).up(5)
arm = cube([30, 10, 6], center=True).up(3).rotz(90).up(10)
show(base | arm)
