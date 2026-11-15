"""pyBOSL2 reference for primitive union, difference and intersection."""

from pybosl2 import cuboid, sphere, xcyl

body = sphere(radius=20)
body = body | cuboid([30, 30, 20]).translate([18, 0, 10])

bore = xcyl(diameter=8, height=60)
body = body - bore

clip = cuboid([50, 50, 30]).up(15)
model = body & clip
