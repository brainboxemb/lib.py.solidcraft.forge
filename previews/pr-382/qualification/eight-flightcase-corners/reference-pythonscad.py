"""PythonSCAD reference: eight 20 mm trihedral protectors around a rounded case.

The sx/sy signs identify which outside face the corner touches. The protector
arms grow inward from that case corner while only their 4 mm plate thickness
extends outward. This matches the Forge component geometry without modelling
its reusable attachment frames.
"""

from pythonscad import *

case = cube([120, 80, 60], center="00-").fillet(8)

def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(hi[i] + lo[i]) / 2 for i in range(3)]
    return cube(size, center=True).translate(center)

def protector(x, y, z, sx, sy, sz):
    # sx/sy point outward; the 20 mm arms therefore extend in -sx/-sy.
    xi = x - sx * 20
    yi = y - sy * 20
    zi = z + sz * 20
    x0, x1 = sorted([x, xi])
    y0, y1 = sorted([y, yi])
    z0, z1 = sorted([z, zi])

    cap = box_bounds(
        [x0, y0, z - 4 if sz > 0 else z],
        [x1, y1, z if sz > 0 else z + 4],
    )
    front = box_bounds(
        [x0, min(y, y + sy * 4), z0],
        [x1, max(y, y + sy * 4), z1],
    )
    side = box_bounds(
        [min(x, x + sx * 4), y0, z0],
        [max(x, x + sx * 4), y1, z1],
    )
    return cap | front | side

model = case
for x, y, z, sx, sy, sz in [
    (-60, -40, 0, -1, -1, 1), (60, -40, 0, 1, -1, 1),
    (60, 40, 0, 1, 1, 1), (-60, 40, 0, -1, 1, 1),
    (-60, -40, 60, -1, -1, -1), (60, -40, 60, 1, -1, -1),
    (60, 40, 60, 1, 1, -1), (-60, 40, 60, -1, 1, -1),
]:
    model = model | protector(x, y, z, sx, sy, sz)
