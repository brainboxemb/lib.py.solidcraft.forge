"""pyBOSL2 geometry reference for the minimal symmetric L bracket."""

from pybosl2 import cuboid

def box_bounds(lo, hi):
    size = [hi[i] - lo[i] for i in range(3)]
    center = [(hi[i] + lo[i]) / 2 for i in range(3)]
    return cuboid(size).translate(center)

horizontal = box_bounds([0, -12, -12], [40, 12, 0])
vertical = box_bounds([0, -12, -40], [12, 12, 0])
(horizontal | vertical).show()
