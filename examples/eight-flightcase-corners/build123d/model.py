"""build123d reference: eight trihedral corner protectors around a case."""
from build123d import Align, Axis, Box, Compound, Pos, fillet


def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(lo[i] + hi[i]) / 2 for i in range(3)]
    return Pos(*center) * Box(*size)


def protector(x, y, z, sx, sy, sz):
    xi, yi, zi = x - sx * 20, y - sy * 20, z + sz * 20
    x0, x1 = sorted((x, xi))
    y0, y1 = sorted((y, yi))
    z0, z1 = sorted((z, zi))
    cap = box_bounds((x0, y0, z-4 if sz>0 else z), (x1, y1, z if sz>0 else z+4))
    front = box_bounds((x0, min(y,y+sy*4), z0), (x1, max(y,y+sy*4), z1))
    side = box_bounds((min(x,x+sx*4), y0, z0), (max(x,x+sx*4), y1, z1))
    return cap + front + side

case = Box(120, 80, 60, align=(Align.CENTER, Align.CENTER, Align.MIN))
case = fillet(case.edges().filter_by(Axis.Z), radius=8)
parts = [case]
for coordinates in [
    (-60,-40,0,-1,-1,1), (60,-40,0,1,-1,1),
    (60,40,0,1,1,1), (-60,40,0,-1,1,1),
    (-60,-40,60,-1,-1,-1), (60,-40,60,1,-1,-1),
    (60,40,60,1,1,-1), (-60,40,60,-1,1,-1),
]:
    parts.append(protector(*coordinates))
model = Compound(children=parts)
