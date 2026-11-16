"""PythonSCAD reference for a box centered on its declared origin."""

from pythonscad import *

length = 40.0
width = 30.0
height = 10.0

model = cube([length, width, height], center=True)
