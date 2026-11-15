"""PythonSCAD geometry reference for a marker at the board's front/top/left corner.

The Forge case is stronger: a fixed topology pick must follow a saved-design
resize in SolidCraft without Python recomputing these coordinates.
"""

from pythonscad import *

board = cube([40, 20, 20], center=True).up(10)
marker = cube([10, 10, 10], center=True).translate([-20, -15, 20])
model = board | marker
