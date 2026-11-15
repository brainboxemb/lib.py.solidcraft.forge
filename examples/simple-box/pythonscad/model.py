"""PythonSCAD reference for the SimpleBox qualification intent.

PythonSCAD can express the same origin convention directly in cube(): the
three-character center code maps to X/Y/Z. PythonSCAD uses "-" for the side
that extends from the datum toward the positive axis, so "00-" means centered
on X and Y and extending from Z=0 to +Z. That matches Forge/SolidCraft Box
without an extra translation.
"""

from pythonscad import *

length = 40.0
width = 30.0
height = 10.0

model = cube([length, width, height], center="00-")
