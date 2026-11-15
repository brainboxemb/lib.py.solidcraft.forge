"""PythonSCAD reference for the SimpleBox qualification intent."""

from pythonscad import *

length = 40.0
width = 30.0
height = 10.0

body = cube([length, width, height], center=True).up(height / 2)
show(body)
