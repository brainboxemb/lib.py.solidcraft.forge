"""PythonSCAD geometry reference for a corner marker with local planar shift.

Forge additionally qualifies that the saved SolidCraft joint follows a changed
shift parameter without rerunning Python.
"""

from pythonscad import *

shift = 5.0
base = cube([40, 30, 20], center=True).up(10)
marker = cube([10, 10, 10], center=True).translate([15, -20, 20])
show(base | marker)
