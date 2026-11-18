"""PythonSCAD reference for a six-hole circular feature pattern."""

from math import cos, pi, sin
from pythonscad import *


plate = cube([100, 100, 6], center=True).up(3)
cutters = None

for index in range(6):
    angle = index * 2 * pi / 6
    x = 30 * cos(angle)
    y = 30 * sin(angle)
    hole = cylinder(d=8, h=12, center=True).translate([x, y, 3])
    cutters = hole if cutters is None else cutters | hole

model = plate - cutters
