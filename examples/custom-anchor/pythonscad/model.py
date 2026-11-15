"""PythonSCAD geometry reference for a rotated arm with a marker at its tip.

Forge additionally qualifies named local AnchorFrame orientation on a reusable
component.
"""

from pythonscad import *

arm = cube([10, 40, 10], center=True).up(5)
marker = cube([10, 10, 10], center=True).translate([0, 20, 5])
model = arm | marker
