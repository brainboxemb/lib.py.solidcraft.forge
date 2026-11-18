"""PythonSCAD reference for a stepped circular body."""

from pythonscad import *

disc = cylinder(d=100, h=10)
hub = cylinder(d=44, h=16).translate([0, 0, 10])
model = disc | hub
