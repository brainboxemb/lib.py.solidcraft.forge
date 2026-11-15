"""PythonSCAD reference for the SimpleBox qualification intent.

PythonSCAD's centered cube convention puts the local origin halfway up the
solid when center=True. Forge/SolidCraft Box uses the bottom face as its native
Z reference. The up(height / 2) below only aligns those coordinate conventions;
it is not additional modelling intent.
"""

from pythonscad import *

length = 40.0
width = 30.0
height = 10.0

model = cube([length, width, height], center=True).up(height / 2)
