"""PythonSCAD geometry reference for the minimal symmetric L bracket."""

from pythonscad import *

def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(hi[i] + lo[i]) / 2 for i in range(3)]
    return cube(size, center=True).translate(center)

horizontal = box_bounds([0, -12, -12], [40, 12, 0])
vertical = box_bounds([0, -12, -40], [12, 12, 0])
model = horizontal | vertical
