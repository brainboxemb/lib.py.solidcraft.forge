"""PythonSCAD geometry reference for an arm with a marker at its +X tip.

Forge additionally demonstrates a named local AnchorFrame with explicit facing
and clocking on a reusable component.
"""

from pythonscad import *

arm = cube([40, 10, 10], center=True).up(5)
marker = cube([10, 10, 10], center=True).translate([20, 0, 5])
model = arm | marker
