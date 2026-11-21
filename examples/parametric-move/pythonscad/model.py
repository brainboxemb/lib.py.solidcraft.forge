"""PythonSCAD geometry reference for two normally translated blocks.

This reference matches the baseline geometry only. Forge separately qualifies
that SolidCraft keeps the translation as a saved parameter expression.
"""

from pythonscad import *

fixed = cube([20, 20, 10], center=True)
moved = cube([20, 20, 10], center=True).right(40)
model = fixed | moved
