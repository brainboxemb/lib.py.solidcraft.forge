"""PythonSCAD reference for the centered SimpleBox qualification intent."""

from pythonscad import *

length = 40.0
width = 30.0
height = 10.0

model = cube([length, width, height], center=True)
