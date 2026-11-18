"""PythonSCAD reference: a centered Ø20 profile extruded from Z=-30 to Z=0."""

from pythonscad import *

profile = circle(d=20)
solid = profile.linear_extrude(height=30).down(30)
model = solid
