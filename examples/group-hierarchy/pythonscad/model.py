"""PythonSCAD geometry reference for the group-hierarchy qualification.

The visible geometry is equivalent. PythonSCAD CSG grouping is not a reference
for SolidCraft browser/BOM component hierarchy persistence.
"""

from pythonscad import *

panel = cube([10, 2, 20], center=True).up(10)
panels = panel | panel.right(11)
frame = cube([35, 10, 40], center=True).up(20).back(20)
model = panels | frame
