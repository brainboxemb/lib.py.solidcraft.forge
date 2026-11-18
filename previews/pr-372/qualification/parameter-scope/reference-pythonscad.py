"""PythonSCAD geometry reference for Forge parameter-scope qualification.

PythonSCAD evaluates these Python values directly; this reference intentionally
does not claim SolidCraft-style saved-design parameter bindings.
"""

from pythonscad import *

shared_width = 80.0

def panel(width):
    return cube([width, 20, 10], center=True).up(5)

model = (
    panel(40)
    | panel(60).right(100)
    | panel(shared_width).right(220)
    | panel(shared_width).right(340)
    | panel(shared_width / 2).right(460)
)
