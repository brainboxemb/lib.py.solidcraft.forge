"""PythonSCAD geometry reference for preserving an already positioned marker.

The marker is bottom-centred before the Z-axis rotation so translating it to
z=15 matches the Forge occurrence pose: its bottom remains at Z=15. The
reference proves visible geometry only; Forge additionally records a native
SolidCraft as-built relationship.
"""

from pythonscad import *

base = cube([40, 30, 10], center="00-")
marker = (
    cube([30, 10, 8], center="00-")
    .rotate([0, 0, 90])
    .translate([50, 20, 15])
)
model = base | marker
