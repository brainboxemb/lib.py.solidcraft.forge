"""CadQuery reference for eight trihedral flightcase corner protectors."""

import cadquery as cq


def box_bounds(lo, hi):
    return cq.Solid.makeBox(
        hi[0] - lo[0],
        hi[1] - lo[1],
        hi[2] - lo[2],
        cq.Vector(lo[0], lo[1], lo[2]),
    )


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
    return cap.fuse(front).fuse(side)


case = (
    cq.Workplane("XY")
    .box(120, 80, 60, centered=(True, True, False))
    .edges("|Z")
    .fillet(8)
    .val()
)

model = cq.Assembly()
model.add(case, name="case")
for index, values in enumerate([
    (-60, -40, 0, -1, -1, 1),
    (60, -40, 0, 1, -1, 1),
    (60, 40, 0, 1, 1, 1),
    (-60, 40, 0, -1, 1, 1),
    (-60, -40, 60, -1, -1, -1),
    (60, -40, 60, 1, -1, -1),
    (60, 40, 60, 1, 1, -1),
    (-60, 40, 60, -1, 1, -1),
]):
    model.add(protector(*values), name=f"protector_{index}")
