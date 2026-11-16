"""build123d reference: sphere/box union, axial bore and intersection."""
from build123d import Box, Cylinder, Pos, Rot, Sphere

sphere = Sphere(20)
box = Pos(18, 0, 10) * Box(30, 30, 20)
body = sphere + box
bore = Rot(0, 90, 0) * Cylinder(4, 120)
clip = Pos(0, 0, 15) * Box(50, 50, 30)
model = (body - bore) & clip
