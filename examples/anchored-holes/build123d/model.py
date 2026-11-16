"""build123d reference for the original lower-left-bottom plate datum."""
from build123d import Align, Box, Cylinder, Pos

width, depth, thickness, spacing = 100.0, 60.0, 10.0, 40.0
plate = Box(
    width,
    depth,
    thickness,
    align=(Align.MIN, Align.MIN, Align.MIN),
)
for y in (depth / 2 - spacing / 2, depth / 2 + spacing / 2):
    plate -= Pos(width / 2, y, thickness / 2) * Cylinder(4.0, thickness + 2)
model = plate
