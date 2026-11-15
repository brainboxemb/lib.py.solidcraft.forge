"""PythonSCAD geometry reference for an assembly-owned inspection datum.

Forge additionally qualifies that the named datum belongs to the assembly and
remains associated with the base corner after native parameter mutation.
"""

from pythonscad import *

base = cube([40, 30, 20], center=True).up(10)
companion = cube([10, 10, 10], center=True).translate([70, 0, 5])
marker = cube([10, 10, 10], center=True).translate([15, -20, 15])
show(base | companion | marker)
