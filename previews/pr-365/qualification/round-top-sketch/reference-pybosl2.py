"""pyBOSL2 reference for a stepped circular body."""

from pybosl2 import cyl

disc = cyl(diameter=100, height=10).translate([0, 0, 5])
hub = cyl(diameter=44, height=16).translate([0, 0, 18])
model = disc | hub
