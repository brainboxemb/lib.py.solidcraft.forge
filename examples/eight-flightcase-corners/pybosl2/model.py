"""pyBOSL2 geometry reference: eight 20 mm trihedral flightcase protectors.

The sx/sy signs identify the outside case faces. Each 20 mm arm grows inward;
only the 4 mm plate thickness projects outside. Forge additionally qualifies
reusable component orientation frames and native attachment relationships.
"""

from pybosl2 import Anchor, cuboid

case = cuboid(
    [120, 80, 60],
    rounding=8,
    edges=Anchor.Z,
    anchor=Anchor.BOTTOM,
)

def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(hi[i] + lo[i]) / 2 for i in range(3)]
    return cuboid(size).translate(center)

def protector(x, y, z, sx, sy, sz):
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
