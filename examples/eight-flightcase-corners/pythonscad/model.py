"""PythonSCAD reference: eight trihedral protectors around a rounded case."""

from pythonscad import *

case = cube([120, 80, 60], center=True).up(30).fillet(8)

def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(hi[i] + lo[i]) / 2 for i in range(3)]
    return cube(size, center=True).translate(center)

def protector(x, y, z, sx, sy, sz):
    # Three 4 mm plates wrapping inward from one case corner.
    x0, x1 = sorted([x, x + sx * 24])
    y0, y1 = sorted([y, y + sy * 24])
    z0, z1 = sorted([z, z + sz * 24])
    cap = box_bounds([x0, y0, z - 4 if sz > 0 else z], [x1, y1, z if sz > 0 else z + 4])
    front = box_bounds([x0, min(y, y + sy * 4), z0], [x1, max(y, y + sy * 4), z1])
    side = box_bounds([min(x, x + sx * 4), y0, z0], [max(x, x + sx * 4), y1, z1])
    return cap | front | side

model = case
for x, y, z, sx, sy, sz in [
    (-60, -40, 0, -1, -1, 1), (60, -40, 0, 1, -1, 1),
    (60, 40, 0, 1, 1, 1), (-60, 40, 0, -1, 1, 1),
    (-60, -40, 60, -1, -1, -1), (60, -40, 60, 1, -1, -1),
    (60, 40, 60, 1, 1, -1), (-60, 40, 60, -1, 1, -1),
]:
    model = model | protector(x, y, z, sx, sy, sz)
