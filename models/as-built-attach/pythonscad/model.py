"""PythonSCAD geometry reference for preserving an already positioned marker.

Both boxes use their centre datum, matching the current Forge Box default from
change 0022. Forge additionally records a native SolidCraft as-built
relationship without re-solving this visible pose.
"""

from pythonscad import *

base = cube([40, 30, 10], center=True)
marker = (
    cube([30, 10, 8], center=True)
    .rotate([0, 0, 90])
    .translate([50, 20, 15])
)
model = base | marker
